"""
Main file of the package.  Kicks off the subcommands.
"""

import logging
import os
import sys
import time

import prompter

import book.cli as cli
import book.session as sess
import book.structure as struct
import book.fs_utils as fs_utils

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)


def arg_parser():
    # logger.info("arg_parser")
    parser = cli.get_parser()
    args = parser.parse_args()
    return args


def main():
    mapping = {
        cli.NEW: show_new,
        cli.RENAME: show_rename,
        cli.SESSION: show_session,
        cli.TRANSFORM: show_transform,
        cli.WORK: show_work,
    }
    args = arg_parser()
    fx = mapping.get(args.command)
    if fx is None:
        show_stats(args)
    else:
        fx(args)


def show_stats(args):
    outline = struct.Outline(args.path)
    outline.reload_dir()
    for scene in outline.scenes(recursive=True):
        print(f"{scene.order:02d}, {scene.count:>5}, {scene.title}")

    print(f"count = {outline.count}")
    print(f"max pk = {outline.max_pk}")


def show_new(args):
    novel_path = fs_utils.find_novel_in_path(args.path)
    print(novel_path)
    if novel_path is None:
        new_novel(args.path, args.convert)
    elif os.path.exists(args.path) and not args.convert:
        print("Novel, folder or scene already exists.")
    else:
        if os.path.splitext(args.path)[1] in (".md", ".txt"):
            new_scene(novel_path, args.path, args.convert)
        else:
            new_folder(novel_path, args.path, args.convert)


def new_novel(path, convert=False):
    print(f"new novel: {path}")
    struct.Novel.create(path, convert)


def new_folder(novel_path, folder_path, convert):
    if not fs_utils.has_order_digit(folder_path):
        print(f"New folders must have an order num (12-new_folder)")
    else:
        print(f"new folder {folder_path} in novel {novel_path}")
        outline = struct.Novel(novel_path).outline
        title = fs_utils.title_from_path(folder_path)
        ID = outline.max_pk + 1
        struct.Folder.create(folder_path, convert, title=title, ID=ID)


def new_scene(novel_path, scene_path, convert):
    if not fs_utils.has_order_digit(scene_path):
        print(f"New scenes must have an order num (12-new_scene)")
    else:
        print(f"new scene {scene_path} in novel {novel_path}")
        outline = struct.Novel(novel_path).outline
        title = fs_utils.title_from_path(scene_path)
        ID = outline.max_pk + 1
        struct.Scene.create(scene_path, convert, title=title, ID=ID)


def show_work(args):
    outline = struct.Outline(args.path)
    pre_changes = outline.auto_rename(dry_run=True)
    for change in pre_changes:
        if change[0] != change[1]:
            print("----" + change[0])
            print("++++" + change[1])
    if not args.dry_run:
        if prompter.yesno("Rename these files?"):
            outline.auto_rename(args.dry_run)
            print("Files renamed.")


def show_session(args):
    def run(session):
        cached = ""
        if not session.is_changed:
            cached = " (cached)"
        print(
            f" {session.count}/{session.goal} - Session; {session.start} start; {session.total_count} total; {cached}                ",
            end="\r",
        )

    novel = struct.Novel(args.path)
    session = sess.Session(novel, args.goal, args.start)
    while True:
        run(session)
        session.commit()
        time.sleep(10)


def show_rename(args):
    outline = struct.Outline(args.path)
    pre_changes = outline.auto_rename(dry_run=True)
    for change in pre_changes:
        if change[0] != change[1]:
            print("----" + change[0])
            print("++++" + change[1])
    if not args.dry_run:
        if prompter.yesno("Rename these files?"):
            outline.auto_rename(args.dry_run)
            print("Files renamed.")


def show_transform(args):
    outline = struct.Outline(args.path)
    if args.softcrlf:
        print("Transforming novel to soft crlf format.")
        outline.transform_soft_crlf()
    if args.hardcrlf:
        print("Transforming novel to hard crlf format.")
        outline.transform_hard_crlf()


if __name__ == "__main__":
    main()
