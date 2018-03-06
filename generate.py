#!/usr/bin/env python3

import os
import codecs
from io import BytesIO
import re
import sys
import textwrap


# vvv These are updated by ./manufacture.py
EXPECTED_NUM_ICONS = 929
FONT_NAME = "fontawesome"
FONT_LICENSE = "CC-BY-SA 4.0: https://github.com/FortAwesome/Font-Awesome/blob/master/LICENSE.txt"
# ^^^ These are updated by ./manufacture.py

if __name__ == "__main__":
    # Make sure we're in the same directory to avoid overwriting things
    file_loc = os.path.dirname(os.path.abspath(__file__))
    curr_dir = os.path.abspath(os.getcwd())

    if file_loc != curr_dir:
        sys.stderr.write(
            "Please execute this script in directory [{0}]\n".format(file_loc)
        )
        sys.exit(1)

    # Make sure the CSS file exists / has been generated
    css_file = os.path.abspath(
        os.path.join(
            file_loc,
            "compiled_fonts",
            FONT_NAME,
            "{name}.css".format(name=FONT_NAME)
        )
    )
    if not os.path.exists(css_file):
        sys.stderr.write(
            "[{0}] does not exist.  Make sure you already generated it (with `rake`).\n".format(
                css_file
            )
        )
        sys.exit(1)

    # Generate header file
    cdefs = []
    num_matches = 0
    longest = 0
    try:
        # fontcusom generates something like
        # .fontname-icon-location:before { content: "\e724"; }
        icon_re = re.compile(r'\.{name}-icon-(.+):before {{ content: "\\(.+)"; }}'.format(name=FONT_NAME))
        with codecs.open(css_file, "r", "utf-8") as css:
            for line in css:
                match = icon_re.match(line)
                if match:
                    num_matches += 1
                    icon_name, icon_code = match.groups()
                    icon_def = "#define {font}_ICON_{icon}".format(
                        font=FONT_NAME.upper(),
                        icon=icon_name.replace("-", "_").upper()
                    )
                    # {code:0>8} format spec says using code variable, align it to
                    # the right and make it a fixed width of 8 characters, padding
                    # with a 0.  AKA zero-fill on the left until 8 char long
                    icon_code = "0x{code:0>8}".format(code=icon_code.upper())
                    cdefs.append((icon_name, icon_def, icon_code))
                    longest = max(longest, len(icon_def))
    except Exception as e:
        sys.stderr.write(
            "Critical: error processing file [{0}]: {1}\n".format(css_file, e)
        )
        sys.exit(1)


    if num_matches == EXPECTED_NUM_ICONS:
        print("Found exactly [{0}] icons, as expected.".format(num_matches))
    else:
        sys.stderr.write(
            "Found [{0}] icons, expected [{1}]\n".format(num_matches,
                                                        EXPECTED_NUM_ICONS)
        )
        sys.exit(1)

    if not os.path.isdir("nanogui"):
        try:
            os.mkdir("nanogui")
        except Exception as e:
            sys.stderr.write(
                "Critical: could not make directory ./nanogui: {0}\n".format(e)
            )
            sys.exit(1)

    containment = "nanogui/{name}".format(name=FONT_NAME)
    if not os.path.isdir(containment):
        try:
            os.mkdir(containment)
        except Exception as e:
            sys.stderr.write(
                "Critical: could not make directory {0}: {1}\n".format(
                    containment, e
                )
            )
            sys.exit(1)

    font_header_file_path = "{containment}/{name}.h".format(
        containment=containment, name=FONT_NAME
    )
    try:
        font_header_file = open(font_header_file_path, "w")
        font_header_file.write(textwrap.dedent(r'''
            /*
                 NanoGUI was developed by Wenzel Jakob <wenzel.jakob@epfl.ch>.
                 The widget drawing code is based on the NanoVG demo application
                 by Mikko Mononen.

                 All rights reserved. Use of this source code is governed by a
                 BSD-style license that can be found in the LICENSE.txt file.

                 This file represents the constants that can be used provided by the
                 {name} font.

                 License: {license}
             */

            /* Developer note: need to make a change to this file?
             * Please raise an Issue on GitHub describing what needs to change.  This file
             * was generated, so the scripts that generated it need to update as well.
             */

            #pragma once

        '''.format(
            name=FONT_NAME,
            license=FONT_LICENSE
        ).replace("\n", "", 1)))  # remove empty line at top

        font_python_bindings_path = "{containment}/constants_{name}.cpp".format(
            containment=containment, name=FONT_NAME
        )
        font_python_bindings = open(font_python_bindings_path, "w")
        font_python_bindings.write(textwrap.dedent('''
            #ifdef NANOGUI_PYTHON

            #include "python.h"
            #include <nanogui/{name}.h>

            /* Python bindings for the {name} font.
             *
             * License: {license}
             */

            /* Developer note: need to make a change to this file?
             * Please raise an Issue on GitHub describing what needs to change.  This file
             * was generated, so the scripts that generated it need to update as well.
             */

            void register_constants_{name}(py::module &m) {{
                /* bindings for the {name} font */
                {{
                    #define C(name) g.attr("ICON_" #name) = py::int_({NAME}_ICON_##name);
                    py::module g = m.def_submodule("{name}");
        '''.format(
            name=FONT_NAME,
            NAME=FONT_NAME.upper(),
            license=FONT_LICENSE
        )))

        # Generate the full header file / python bindings
        for icon_name, icon_def, icon_code in cdefs:
            # icon_def is `#define {FONT_NAME.upper()}_ICON_X`

            # Generate the header file #define directive
            font_header_file.write("{definition:<{longest}} {code}\n".format(
                definition=icon_def,
                longest=longest,
                code=icon_code
            ))

            # Generate the python binding
            cpp_def = icon_def.split(" ")[1]
            py_def  = cpp_def.split("{NAME}_ICON_".format(NAME=FONT_NAME.upper()))[1]
            pybind  = "C({0});".format(py_def)
            py_name = "ICON_{0}".format(py_def)
            font_python_bindings.write("        {pybind}\n".format(pybind=pybind))

        # close the pybind
        font_python_bindings.write(textwrap.dedent('''
                    #undef C
                }
            }

            #endif
        '''))

        font_header_file.close()
        font_python_bindings.close()

        # generate the example icon programs
        cpp_example_path = "{containment}/example_{name}.cpp".format(
            containment=containment, name=FONT_NAME
        )
        cpp_example = open(cpp_example_path, "w")

        # write the header of the cpp example
        cpp_example.write(textwrap.dedent(r'''
            /* Developer note: need to make a change to this file?
             * Please raise an Issue on GitHub describing what needs to change.  This file
             * was generated, so the scripts that generated it need to update as well.
             */

            #include <nanogui/nanogui.h>
            #include <nanogui/resources.h>
            #include <nanogui/{name}.h>
            using namespace nanogui;

            // Custom theme for loading the {name} font
            class {Name}Theme : public nanogui::Theme {{
            public:
                // This override informs NanoGUI to use this as the icon font.
                virtual std::string defaultIconFont() const override {{ return "{name}"; }}

                {Name}Theme(NVGcontext *ctx) : nanogui::Theme(ctx) {{
                    // load the {name} font into memory
                    m{Name}Font = nanogui::createFontMem(ctx, "{name}", "{name}.ttf");
                    if (m{Name}Font == -1)
                        throw std::runtime_error("Could not load the {name} font!");

                    // TODO: you need to override the following default icon choices in your
                    //       own application!  See documentation for nanogui::Theme.
                    // mCheckBoxIcon             = ENTYPO_ICON_CHECK;
                    // mCheckBoxIconExtraScale   = defaultCheckBoxIconExtraScale();
                    // mMessageInformationIcon   = ENTYPO_ICON_INFO_WITH_CIRCLE;
                    // mMessageQuestionIcon      = ENTYPO_ICON_HELP_WITH_CIRCLE;
                    // mMessageWarningIcon       = ENTYPO_ICON_WARNING;
                    // mMessageAltButtonIcon     = ENTYPO_ICON_CIRCLE_WITH_CROSS;
                    // mMessagePrimaryButtonIcon = ENTYPO_ICON_CHECK;
                    // mPopupChevronRightIcon    = ENTYPO_ICON_CHEVRON_RIGHT;
                    // mPopupChevronLeftIcon     = ENTYPO_ICON_CHEVRON_LEFT;
                    // mPopupIconExtraScale      = defaultPopupIconExtraScale();
                    // mTabHeaderLeftIcon        = ENTYPO_ICON_ARROW_BOLD_LEFT;
                    // mTabHeaderRightIcon       = ENTYPO_ICON_ARROW_BOLD_RIGHT;
                    // mTextBoxUpIcon            = ENTYPO_ICON_CHEVRON_UP;
                    // mTextBoxDownIcon          = ENTYPO_ICON_CHEVRON_DOWN;
                    // mTextBoxIconExtraScale    = defaultTextBoxIconExtraScale();
                }}

                virtual ~{Name}Theme() {{ /* nothing to free */ }}

            protected:
                int m{Name}Font = -1;
            }};

            class {Name}Screen : public nanogui::Screen {{
            public:
                {Name}Screen(const Vector2i &size, const std::string &title, bool resizable)
                    : nanogui::Screen(size, title, resizable) {{

                    m{Name}Theme = new {Name}Theme(this->mNVGContext);
                    this->setTheme(m{Name}Theme);
                }}

                virtual ~{Name}Screen() {{ /* nothing to free */ }}

                // allow <ESCAPE> to exit
                virtual bool keyboardEvent(int key, int scancode, int action, int modifiers) override {{
                    if (key == GLFW_KEY_ESCAPE && modifiers == 0) {{
                        setVisible(false);
                        return true;
                    }}

                    return Screen::keyboardEvent(key, scancode, action, modifiers);
                }}

            protected:
                nanogui::ref<{Name}Theme> m{Name}Theme;
            }};


            // Convenience macro for creating an IconBox. Make sure you put a semicolon after the call to this macro!
            #define ADD_ICON(parent, icon, boxWidth) \
                new IconBox(parent, #icon, icon, boxWidth)

            class IconBox : public Widget {{
            public:
                IconBox(Widget *parent, const std::string &name, int icon, int width)
                    : Widget(parent) {{

                    this->setLayout(new BoxLayout(Orientation::Horizontal));

                    auto *b = new Button(this, "", icon);
                    b->setFixedWidth(40);

                    auto *text = new TextBox(this, name);
                    text->setDefaultValue(name);
                    text->setEditable(true);
                    /* Return false essentially makes it not possible to actually edit this text
                     * box, but keeping it editable=true allows selection for copy-paste.  If the
                     * text box is not editable, then the user cannot highlight it.
                     */
                    text->setCallback([](const std::string &) {{ return false; }});
                    text->setFont("mono-bold");
                    text->setFixedWidth(width - 40);
                }}
            }};


            int main(int /* argc */, char ** /* argv */) {{
                nanogui::init();

                /* scoped variables */ {{
                    static constexpr int width      = 1000;
                    static constexpr int half_width = width / 2;
                    static constexpr int height     = 800;

                    // create a fixed size screen with one window
                    {Name}Screen *screen = new {Name}Screen({{width, height}}, "NanoGUI {Name} Icons", false);

                    // create the custom theme now so that all children will inherit it
                    Window *window = new Window(screen, "");
                    window->setPosition({{0, 0}});
                    window->setFixedSize({{width, height}});

                    // attach a vertical scroll panel
                    auto vscroll = new VScrollPanel(window);
                    vscroll->setFixedSize({{width, height}});

                    // vscroll should only have *ONE* child. this is what `wrapper` is for
                    auto wrapper = new Widget(vscroll);
                    wrapper->setFixedSize({{width, height}});
                    wrapper->setLayout(new GridLayout());// defaults: 2 columns

                    ////////////////////////////////////////////////////////////////////////
                    ////////////////////////////////////////////////////////////////////////
                    ////////////////////////////////////////////////////////////////////////
        '''.format(
            name=FONT_NAME,
            Name=FONT_NAME.capitalize()
        )).lstrip())

        for icon_name, icon_def, icon_code in cdefs:
            # icon_def is `#define FONTNAME_ICON_X`
            cpp_def = icon_def.split(" ")[1]
            cpp_example.write("        ADD_ICON(wrapper, {cpp_def}, half_width);\n".format(cpp_def=cpp_def))

        # close out the cpp example
        cpp_example.write(textwrap.dedent('''
                    ////////////////////////////////////////////////////////////////////////
                    ////////////////////////////////////////////////////////////////////////
                    ////////////////////////////////////////////////////////////////////////

                    screen->performLayout();
                    screen->setVisible(true);

                    nanogui::mainloop();
                }

                nanogui::shutdown();
                return 0;
            }
        ''').replace("\n", "", 1))
        cpp_example.close()

        # <3 python
        py_example_path = "{containment}/example_{name}.py".format(
            containment=containment, name=FONT_NAME
        )
        with open(py_example_path, "w") as py_example:
            py_example.write(textwrap.dedent('''
                # Developer note: need to make a change to this file?
                # Please raise an Issue on GitHub describing what needs to change.  This file
                # was generated, so the scripts that generated it need to update as well.

                import gc

                import nanogui
                from nanogui import Screen, Window, Widget, GridLayout, VScrollPanel, Button, TextBox, BoxLayout, Orientation, Theme
                from nanogui import {name}


                class {Name}Theme(nanogui.Theme):
                    # This override informs NanoGUI to use this as the icon font.
                    def defaultIconFont(self):
                        return "{name}"

                    def __init__(self, ctx):
                        super({Name}Theme, self).__init__(ctx)
                        self.m{Name}Font = nanogui.createFontMem(ctx, "{name}", "{name}.ttf")
                        if self.m{Name}Font == -1:
                            raise RuntimeError("Could not load the {name} font!")

                        # TODO: you need to override the following default icon choices in your
                        #       own application!  See documentation for nanogui::Theme.
                        # self.mCheckBoxIcon             = entypo.ICON_CHECK
                        # self.mCheckBoxIconExtraScale   = self.defaultCheckBoxIconExtraScale()
                        # self.mMessageInformationIcon   = entypo.ICON_INFO_WITH_CIRCLE
                        # self.mMessageQuestionIcon      = entypo.ICON_HELP_WITH_CIRCLE
                        # self.mMessageWarningIcon       = entypo.ICON_WARNING
                        # self.mMessageAltButtonIcon     = entypo.ICON_CIRCLE_WITH_CROSS
                        # self.mMessagePrimaryButtonIcon = entypo.ICON_CHECK
                        # self.mPopupChevronRightIcon    = entypo.ICON_CHEVRON_RIGHT
                        # self.mPopupChevronLeftIcon     = entypo.ICON_CHEVRON_LEFT
                        # self.mPopupIconExtraScale      = self.defaultPopupIconExtraScale()
                        # self.mTabHeaderLeftIcon        = entypo.ICON_ARROW_BOLD_LEFT
                        # self.mTabHeaderRightIcon       = entypo.ICON_ARROW_BOLD_RIGHT
                        # self.mTextBoxUpIcon            = entypo.ICON_CHEVRON_UP
                        # self.mTextBoxDownIcon          = entypo.ICON_CHEVRON_DOWN
                        # self.mTextBoxIconExtraScale    = self.defaultTextBoxIconExtraScale()


                class EscapeScreen(nanogui.Screen):
                    def __init__(self, size, title, resizable):
                        super(EscapeScreen, self).__init__(size, title, resizable)

                    # allow <ESCAPE> to exit
                    def keyboardEvent(self, key, scancode, action, modifiers):
                        if key == nanogui.glfw.KEY_ESCAPE and modifiers == 0:
                            self.setVisible(False)
                            return True

                        return super(EscapeScreen, self).keyboardEvent(key, scancode, action, modifiers)


                class IconBox(nanogui.Widget):
                    def __init__(self, parent, name, icon, width):
                        super(IconBox, self).__init__(parent)

                        self.setLayout(nanogui.BoxLayout(nanogui.Orientation.Horizontal))

                        b = nanogui.Button(self, "", icon)
                        b.setFixedWidth(40)

                        text = nanogui.TextBox(self, name)
                        text.setDefaultValue(name)
                        text.setEditable(True)
                        # Return false essentially makes it not possible to actually edit this text
                        # box, but keeping it editable=true allows selection for copy-paste.  If the
                        # text box is not editable, then the user cannot highlight it.
                        text.setCallback(lambda x: False)
                        text.setFont("mono-bold")
                        text.setFixedWidth(width - 40)


                if __name__ == "__main__":
                    nanogui.init()

                    width      = 1000
                    half_width = width // 2
                    height     = 800

                    # create a fixed size screen with one window
                    screen = EscapeScreen((width, height), "NanoGUI {Name} Icons", False)

                    # NOTE: if doing a custom screen derived class, for some reason if you
                    #       load a custom theme object and call setTheme in the constructor
                    #       of the derived theme class it will not work.  You can load the
                    #       theme in the constructor, but just make sure to call setTheme
                    #       after the constructor is finished (as we are doing here)
                    #
                    #       Setting the theme of the screen means that all children created
                    #       after this point will use this as their theme (rather than the
                    #       default NanoGUI theme).
                    theme = {Name}Theme(screen.nvgContext())
                    screen.setTheme(theme)
                    window = Window(screen, "")
                    window.setPosition((0, 0))
                    window.setFixedSize((width, height))

                    # attach a vertical scroll panel
                    vscroll = VScrollPanel(window)
                    vscroll.setFixedSize((width, height))

                    # vscroll should only have *ONE* child. this is what `wrapper` is for
                    wrapper = Widget(vscroll)
                    wrapper.setFixedSize((width, height))
                    wrapper.setLayout(GridLayout())  # defaults: 2 columns

                    # NOTE: don't __dict__ crawl in real code!
                    # this is just because it's more convenient to do this for enumerating all
                    # of the icons -- see cpp example for alternative...
                    for key in {name}.__dict__.keys():
                        if key.startswith("ICON_"):
                            IconBox(wrapper, key, {name}.__dict__[key], half_width)

                    screen.performLayout()
                    screen.drawAll()
                    screen.setVisible(True)

                    nanogui.mainloop()

                    del screen
                    gc.collect()

                    nanogui.shutdown()
            '''.format(
                name=FONT_NAME,
                Name=FONT_NAME.capitalize()
            )).lstrip())
    except Exception as e:
        sys.stderr.write(
            "Critical: unknown error generating NanoGUI utilities: {0}\n".format(e)
        )
        sys.exit(1)

