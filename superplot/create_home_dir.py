"""
A utility script to create a home directory containing config files and examples at a specified location.
"""

from argparse import ArgumentParser as arg_parser
import os
import sys
import shutil
import warnings
from distutils.util import strtobool


def prompt(query):
    """ yes/no/y/n user prompt helper function """
    sys.stdout.write('%s [y/n]: ' % query)
    val = raw_input()
    try:
        ret = strtobool(val)
    except ValueError:
        sys.stdout.write('Please answer with a y/n\n')
        return prompt(query)
    return ret


def main():
    parser = arg_parser(description='Superplot home directory setup', conflict_handler='resolve')

    parser.add_argument('--dir',
                        '-d',
                        help='Location of user home directory',
                        type=str,
                        required=True)

    args = vars(parser.parse_args())

    # Create target directory if it doesn't exist

    user_dir = os.path.abspath(args['dir'])
    try:
        if not os.path.isdir(user_dir):
            os.mkdir(user_dir)
    except OSError as e:
        warnings.warn(
            "Could not create home directory: {}".format(
                e.strerror
            )
        )
        sys.exit(1)

    # Drop text file with user home dir location in script directory
    script_dir = os.path.dirname(os.path.realpath(__file__))
    home_dir_file = os.path.join(script_dir, "user_home.txt")
    with open(home_dir_file, "wb") as f:
        f.write(user_dir)

    # Copy yaml files. Prompt user to overwrite if already present.
    yaml_names = ["schemes.yml", "options.yml"]
    config_paths = [os.path.join(user_dir, name) for name in yaml_names]
    copy_config = True

    if any([os.path.exists(path) for path in config_paths]):

        print "yaml files already present. Please note that yamls files " \
              "distributed with previous versions of superplot may not work with " \
              "this release. If you wish to compare your customised yamls with " \
              "the current defaults, they are distributed with the source code " \
              "(superplot/{}).".format(yaml_names)

        copy_config = prompt("Replace existing files: {}".format(config_paths))

    copy_from = [os.path.join(script_dir, name) for name in yaml_names]

    if copy_config:
        for (from_, to) in zip(copy_from, config_paths):
            try:
                shutil.copy(from_, to)
            except shutil.Error as e:
                warnings.warn(
                        "Error copying yaml file to user directory: {}".format(
                                e.strerror
                        )
                )

    # Copy style sheets to user directory
    styles_dir = os.path.join(user_dir, "styles")
    copy_style_sheets = True

    if os.path.isdir(styles_dir):
        copy_style_sheets = prompt("Replace existing style sheets: {}".format(styles_dir))
        if copy_style_sheets:
            try:
                shutil.rmtree(styles_dir)
            except shutil.Error as e:
                warnings.warn(
                    "Error removing existing style sheets: {}".format(
                        e.strerror
                    )
                )

    if copy_style_sheets:
        try:
            copy_from = os.path.join(script_dir, "plotlib/styles")
            shutil.copytree(copy_from, styles_dir)
        except shutil.Error as e:
            warnings.warn(
                    "Error copying style sheets to user directory: {}".format(
                            e.strerror
                    )
            )

    # Copy example data to user directory
    example_dir = os.path.join(user_dir, "example")
    copy_examples = True

    if os.path.isdir(example_dir):
        copy_examples = prompt("Replace existing example files: {}".format(example_dir))
        if copy_examples:
            try:
                shutil.rmtree(example_dir)
            except shutil.Error as e:
                warnings.warn(
                    "Error removing existing example files: {}".format(
                        e.strerror
                    )
                )

    if copy_examples:
        try:
            copy_from = os.path.join(script_dir, "example")
            shutil.copytree(copy_from, example_dir)
        except shutil.Error as e:
            warnings.warn(
                    "Error copying example files to user directory: {}".format(
                            e.strerror
                    )
            )

if __name__ == '__main__':
    main()
