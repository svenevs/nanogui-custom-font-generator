#!/usr/bin/env python3

import argparse
import os
import re
import sys
import textwrap

def manufacture_foncutstom_config(ymlPath, fontName):
    config_yml = textwrap.dedent('''
        font_name: "{fontName}"
        # VERY IMPORTANT!  The css_selector must be EXACTLY
        #     ".{{{{font_name}}}}-icon-{{{{glyph}}}}"
        # Otherwise generate.py will NOT be able to parse the generated css file!
        css_selector: ".{fontName}-icon-{{{{glyph}}}}"
        preprocessor_path: ""
        # you can try setting autowidth to 'true', but it may not look right
        # what this does is try and scale the icons to be the same size.  on some
        # fonts, it may be necessary.  on others, it may produce shearing.
        autowidth: false
        no_hash: true
        force: false
        debug: false
        quiet: false

        input:
            vectors: "icons/{fontName}"

        # All output placed in one location
        output:
            fonts: "compiled_fonts/{fontName}"
            css:   "compiled_fonts/{fontName}"

        templates:
        - scss
        - css
        - preview
    '''.format(fontName=fontName))

    # write to config/fontcustom.yml
    try:
        with open(ymlPath, "w") as yml:
            yml.write(config_yml)
    except Exception as e:
        sys.stderr.write(
            "Critical error: could not write to the file {0}: {1}\n".format(
                ymlPath, e
            )
        )
        sys.exit(1)


def manufacture_generate(generatePath, fontName, fontLicense, numIcons):
    # First read in all of the contents
    try:
        with open(generatePath, "r") as generate:
            contents = generate.read()

    except Exception as e:
        sys.stderr.write(
            "Critical error: could not read the file {0}: {1}\n".format(
                generatePath, e
            )
        )
        sys.exit(1)

    # There are three lines we need to change at the top:
    # EXPECTED_NUM_ICONS = some number
    # FONT_NAME = "fontname"
    # FONT_LICENSE = "license name and url"
    regex_base         = r"^{VAR} = .*"
    num_icons_regex    = regex_base.format(VAR="EXPECTED_NUM_ICONS")
    font_name_regex    = regex_base.format(VAR="FONT_NAME")
    font_license_regex = regex_base.format(VAR="FONT_LICENSE")

    num_icons_fixed    = False
    font_name_fixed    = False
    font_license_fixed = False

    fixed_contents = []
    for line in contents.splitlines():
        # if already modified, simply paste the rest of the script
        if num_icons_fixed and font_name_fixed and font_license_fixed:
            fixed_contents.append(line)
        else:
            if not num_icons_fixed:
                match = re.match(num_icons_regex, line)
                if match:
                    fixed_contents.append("EXPECTED_NUM_ICONS = {0}".format(numIcons))
                    num_icons_fixed = True
                    continue

            if not font_name_fixed:
                match = re.match(font_name_regex, line)
                if match:
                    fixed_contents.append('FONT_NAME = "{0}"'.format(fontName))
                    font_name_fixed = True
                    continue

            if not font_license_fixed:
                match = re.match(font_license_regex, line)
                if match:
                    fixed_contents.append('FONT_LICENSE = "{0}"'.format(fontLicense))
                    font_license_fixed = True
                    continue

            # Otherwise just add the line
            fixed_contents.append(line)

    if num_icons_fixed and font_name_fixed and font_license_fixed:
        try:
            with open(generatePath, "w") as generate:
                generate.write("{0}\n".format("\n".join(line for line in fixed_contents)))
        except Exception as e:
            sys.stderr.write(
                "Critical error: could not write the file {0}: {1}\n".format(
                    generatePath, e
                )
            )
            sys.exit(1)
    else:
        sys.stderr.write(textwrap.dedent('''
            There was an issue modifying {0}.

            One or more of the three lines that need to be modified were not patched:

            - EXPECTED_NUM_ICONS patched? {1}
            - FONT_NAME patched?          {2}
            - FONT_LICENSE patched?       {3}
        '''.format(generatePath, num_icons_fixed, font_name_fixed, font_license_fixed)))
        sys.exit(1)


if __name__ == "__main__":
    here = os.path.abspath(os.path.dirname(__file__))
    curr = os.path.abspath(os.curdir)
    if curr != here:
        sys.stderr.write(textwrap.dedent('''\
            Please run this script from the same directory

                cd "{here}"
        '''.format(here=here)))
        sys.exit(1)

    icons_dir = os.path.join(here, "icons")
    font_names = os.listdir(icons_dir)
    if len(font_names) == 0:
        sys.stderr.write("There are no subdirectories under {0}\n".format(icons_dir))
        sys.exit(1)

    font_dirs = []
    for potential_dir in font_names:
        dir_path = os.path.join(icons_dir, potential_dir)
        if os.path.isdir(dir_path):
            font_dirs.append(potential_dir)

    if not font_dirs:
        sys.stderr.write(
            "There is only 'fontawesome' in '{0}', which has already been generated.\n".format(
                icons_dir
            )
        )
        sys.exit(1)

    for font in font_dirs:
        match = re.match(r"^[a-zA-Z]{1}[a-zA-Z0-9]*$", font)
        if not match:
            sys.stderr.write(textwrap.dedent('''\
                The directory icons/{dir} cannot be used.

                Icon font names must satisfy the following requirements:

                1. They consist of only upper or lower case letters and digits.
                2. They start with either an upper or lower case letter.

                So fonts with e.g. a hyphen, or an underscore, or any other special
                symbols cannot be used.

                Simply rename the directory to satisfy these requirements.
            '''.format(dir=font)))
            sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "font_name",
        help="The font name to manufacture.",
        choices=font_dirs
    )

    args = parser.parse_args()
    font_name = args.font_name

    # determine how many icons there are
    font_dir = os.path.join(icons_dir, font_name)
    if not os.path.isdir(font_dir):
        sys.stderr.write("Internal error: [{0}] is not a directory?\n".format(font_dir))
        sys.exit(1)

    all_icons = [icon for icon in os.listdir(font_dir) if icon.endswith(".svg")]
    if len(all_icons) == 0:
        sys.stderr.write(
            "Error: there are no .svg icons in the directory {0}\n".format(font_dir)
        )
        sys.exit(1)

    num_icons = len(all_icons)
    print(">>> Found {0} icons in {1}.".format(num_icons, font_dir))

    # Get the license information
    if sys.version[0] == "3":
        user_input = lambda x: input(x)
    else:
        user_input = lambda x: raw_input(x)

    print(textwrap.dedent('''\
        >>> Please enter the license information for the {font_name} font, including a
            URL to the official license.  For example, the Font Awesome 5 Free license
            icons are governed by CC-BY-SA 4.0, so you would enter:

                CC-BY-SA 4.0: https://github.com/FortAwesome/Font-Awesome/blob/master/LICENSE.txt

            Any input without 'http' in it will be rejected.  Input must be on one line.
    '''.format(
        font_name=font_name
    )))
    try:
        license = user_input("   license> ")
    except:
        sys.stderr.write("\n\nGoodbye...\n")
        sys.exit(1)

    if "http" not in license:
        sys.stderr.write(textwrap.dedent('''
            Please include a URL to the official license of the font you wish to embed
            into NanoGUI.  The license information is included in the generated header
            file and python bindings.
        '''))
        sys.exit(1)

    if len(license.split(r"\n")) > 1 or len(license.split(r"\r")) > 1:
        sys.stderr.write(textwrap.dedent('''
            The license information must be on one line, make sure there are no newline
            characters or carriage returns in the input you provided.
        '''))
        sys.exit(1)


    # Update configs/fontcustom.yml
    print(">>> Updating configs/fontcustom.yml.")
    manufacture_foncutstom_config(
        os.path.join(here, "config", "fontcustom.yml"),
        font_name
    )

    print(">>> Updating generate.py.")
    manufacture_generate(
        os.path.join(here, "generate.py"),
        font_name,
        license,
        num_icons
    )

    sys.stdout.write(textwrap.dedent('''\
        Done!

        First, execute 'rake' in this directory.

        Then, run './generate.py' (or 'python generate.py' if you do not have python **3** installed).
    '''))


