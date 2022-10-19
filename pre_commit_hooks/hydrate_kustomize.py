#!/usr/bin/env python3

import errno
import logging
import os
import pathlib
import shutil
import subprocess
import types
from functools import cache

import git

logging.basicConfig(
    level=os.environ.get("LOGLEVEL", "INFO"),
)

log = logging.getLogger("hydrate")


@cache
def get_git_root():
    git_repo = git.Repo()
    return git_repo.working_tree_dir


@cache
def get_wet_dir(app, env):
    return f"{get_git_root()}/wet/applications/{app}/envs/{env}"


@cache
def get_dry_dir(app, env):
    return f"{get_git_root()}/dry/applications/{app}/envs/{env}"


def prepare_wet_dir(app, env):
    wet_dir = get_wet_dir(app, env)
    pathlib.Path(wet_dir).mkdir(parents=True, exist_ok=True)
    # soft-link direnv files for env
    force_symlink(
        f"{get_git_root()}/dry/envs/global/.envrc",
        f"{wet_dir}/.envrc"
    )
    force_symlink(
        f"{get_git_root()}/dry/envs/{env}/.env",
        f"{wet_dir}/.env"
    )


def force_symlink(src, dst):
    try:
        os.symlink(src, dst)
    except OSError as e:
        if e.errno == errno.EEXIST:
            os.remove(dst)
            os.symlink(src, dst)


def remove_prefix(text, prefix):
    if text.startswith(prefix):
        start = len(prefix)
        return text[start:]
    else:
        return text


def get_dry_and_wet_apps():
    result = []
    for root, _, _ in os.walk(get_git_root()):
        path = remove_prefix(root, get_git_root())
        path = remove_prefix(path, "/")
        path_segments = path.split("/")
        if (
            len(path_segments) == 5
            and path_segments[1] == "applications"
            and path_segments[3] == "envs"
        ):
            type = path_segments[0]
            app = path_segments[2]
            env = path_segments[4]
            log.debug(f"Found type={type},app={app},env={env}")
            result.append(types.SimpleNamespace(app=app, env=env, type=type))
    return result

def hydrate_instance(app, env):
    log.info(f"Hydrating app={app},env={env}")
    p = subprocess.Popen(
        [
            "kustomize",
            "build",
            "--enable-alpha-plugins",
            "--enable-exec",
            "--enable-helm",
            "-o",
            f"{get_wet_dir(app, env)}/generated.k8s.yaml",
        ],
        cwd=get_dry_dir(app, env),
    )
    p.wait()


def prune_instance(app, env):
    log.info(f"Pruning app={app},env={env}")
    shutil.rmtree(f"{get_wet_dir(app, env)}", ignore_errors=True)


def hydrate(dry):
    for item in dry:
        prepare_wet_dir(item.app, item.env)
        hydrate_instance(item.app, item.env)


def prune(dry, wet):
    difference = [item for item in wet if item not in dry]
    for item in difference:
        prune_instance(item.app, item.env)


def reconcile():
    app_list = get_dry_and_wet_apps()
    dry = [
        types.SimpleNamespace(app=item.app, env=item.env)
        for item in app_list
        if item.type == "dry"
    ]
    wet = [
        types.SimpleNamespace(app=item.app, env=item.env)
        for item in app_list
        if item.type == "wet"
    ]

    prune(dry, wet)
    hydrate(dry)
    git_repo = git.Repo()
    git_repo.git.add("wet", A=True)


def main():
    return reconcile()


if __name__ == "__main__":
    SystemExit(main())
