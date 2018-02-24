# nanogui-custom-font-generator

A skeleton repository containing scripts to generate TTF fonts from SVG, and bind those
fonts with [NanoGUI][nanogui].

# Overview

The goal of this repository is to enable [NanoGUI][nanogui] users to be able to embed
their own custom icon fonts for use with their applications.  The proceedings are as
follows:

Here are the abbreviated instructions.

1. Create a new directory underneath `icons/`.  For example, `mkdir icons/fontname`.
   For best results, make sure `fontname` is all lower-case alphabetic letters only (no
   hyphens, underscores, special symbols, etc).
2. Copy all of the `.svg` images to `icons/fontname`.
3. Run `./manufacture.py fontname` (or `python manufacture.py fontname` for python **2**).
4. Run `rake` to compile the fonts.
5. Run `./generate.py` (or `python generate.py` for python **2**) to create the NanoGUI
   header file, python bindings, and icon demo applications.
6. The NanoGUI generated utilities are now under `nanogui/fontname`.  See the
   [Use the Utilities](#use-the-utilities) section at the end for what to do with these.

Everything that follows is a description of the exact requirements, as well as potential
changes you will need to make.

**Contents**

- [Generating the TTF Font](#generating-the-ttf-font)
    - [Install `fontcustom`](#install-fontcustom)
    - [Get the Font Icons Ready](#get-the-font-icons-ready)
        - [Preparing a Flat Directory](#preparing-a-flat-directory)
        - [Naming Conventions](#naming-conventions)
    - [Update the `fontcustom` Configs and Generate Script](#update-the-fontcustom-configs-and-generate-script)
        - [How to Update](#how-to-update)
        - [What Needs to Update](#what-needs-to-update)
    - [Generate the Font](#generate-the-font)
- [Generate the NanoGUI Utilities](#generate-the-nanogui-utilities)
    - [Generate the Utilities](#generate-the-utilities)
    - [Use the Utilities](#use-the-utilities)
- [License](#license)

# Generating the TTF Font

## Install `fontcustom`

First, you will need to follow the
[installation instructions](https://github.com/FontCustom/fontcustom#installation)
for `fontcustom`.  This is the tool that will enable us to take a directory of SVG
images and turn them into a TTF font.

## Get the Font Icons Ready

You are welcome to fork this repository, but once you have all of the files generated
once you generally won't need it anymore.  The choice is yours, but these instructions
demonstrate how to just generate it all locally.

```console
# Download this repository
$ https://github.com/svenevs/nanogui-custom-font-generator.git

# Enter the top-level
$ cd nanogui-custom-font-generator/
```

Lets suppose that you wanted to generate a TTF font named `myicons`.  Then we will store
these icons in `icons/myicons`:

```console
# Create a containment directory
$ mkdir icons/myicons

# Copy all of the SVG images from this font from wherever you have them
$ cp ~/Downloads/myicons-2.3/*.svg icons/myicons
```

There are a couple of things to be aware of when coordinating this structure.  The first
is that we want a flat directory.  The second is naming conventions, since we are
ultimately embedding this in a C++ program using `#define` directives, special
characters are not allowed.

### Preparing a Flat Directory

If you already have a flat directory structure of all of the SVG icons, you should be
good to go.  Skip ahead to the [Naming Conventions](#naming-conventions) section.

In the preparation of [`icons/fontawesome`](icons/fontawesome), when I originally
downloaded [Font Awesome 5 Free v5.0.6](https://fontawesome.com/), their font was structured into
three different primary packages: `brands`, `solid`, and the `regular` icons.  Some of
the names are duplicates, so we want to make sure that when creating the flat directory
we don't lose icons.  The process looked like this:

```console
# Go to where you downloaded your font and unpack
$ cd Downloads
$ unzip fontawesome-free-5.0.6.zip

# For Font Awesome 5 Free, this is where the raw SVG images are
$ cd fontawesome-free-5.0.6/advanced-options/raw-svg/

$ ls
brands/  regular/ solid/
```

To prevent overwriting images, the following was sufficient:

```console
# Make a containment directory
$ mkdir fontawesome

# For this first example, we'll `echo` before executing to make sure
# it will do what we want: take brands/icon.svg and copy it to be
# fontawesome/brands-icon.svg.
$ for icon in $(ls brands/*.svg); do echo "cp $icon fontawesome/brands-$(basename $icon)"; done

# Copy all of the brands icons with a `brands` prefix
$ for icon in $(ls brands/*.svg); do cp $icon fontawesome/brands-$(basename $icon); done

# Copy all of the solid icons with a `solid` prefix
$ for icon in $(ls solid/*.svg); do cp $icon fontawesome/solid-$(basename $icon); done

# Copy all of the regular icons without any prefix
$ for icon in $(ls regular/*.svg); do cp $icon fontawesome/; done
```

It's a good idea to verify that the total number of icons you have in this flat
directory matches the number you expected.  In this case, Font Awesome 5 Free has 929
icons.  **Knowing how many icons there are is a requirement for a later phase**.

```console
$ find fontawesome -name *.svg | wc -l
929
```

### Naming Conventions

Depending on the icon font you are creating, you may need to take additional steps to
enable it to be used in NanoGUI.  For example, when updating NanoGUI's default icon
font (Entypo+), there were three icons that needed to have both the file name changed,
as well as the SVG itself edited.  SVG icons, fortunately, can be edited with your
favorite text editor!  In this case, the issue was two icons had a `+` character, and
one icon had a `%` character.  For web applications, this is ok, but for C++ you would
end up with invalid syntax

```cpp
//                     v
#define SOME_ICON_WITH_+ 0xFFFF
//                     ^
```

Refer to [the minor divergence section][divergence] of the Entypo+ generation utility
for how to fix that.

[divergence]: https://github.com/svenevs/nanogui-entypo#minor-divergence-from-entypo

## Update the `fontcustom` Configs and Generate Script

Now that you have all of your icons in `icons/fontname/*.svg`, we need to update the
font generation utilities and nanogui generation utilities.  I've written a helper
script to do this for you, called `manufacture.py`.

### How to Update

You should be able to just run the `manufacture.py` script.  You must run it from the
top-level `nanogui-custom-font-generator` directory.  Note that the shebang at the top
of the file is for Python **3**.  If you have `python3` installed, simply execute
`./manufacture.py`.  If you do not, run `python manufacture.py` instead.

Here's an example run when generating the
[typicons](https://github.com/stephenhutchings/typicons.font) font, noting that I
already made the directory `icons/typicons` and copied the SVG images there.

```console
$ ./manufacture.py typicons
>>> Found 336 icons in /Users/sven/Desktop/nanogui-custom-font-demo/resources/nanogui-custom-font-generator/icons/typicons.
>>> Please enter the license information for the typicons font, including a
    URL to the official license.  For example, the Font Awesome 5 Free license
    icons are governed by CC-BY-SA 4.0, so you would enter:

        CC-BY-SA 4.0: https://github.com/FortAwesome/Font-Awesome/blob/master/LICENSE.txt

    Any input without 'http' in it will be rejected.  Input must be on one line.

    license> CC-BY-SA 3.0: https://github.com/stephenhutchings/typicons.font#license
>>> Updating configs/fontcustom.yml.
>>> Updating generate.py.
Done!

First, execute 'rake' in this directory.

Then, run './generate.py' (or 'python generate.py' if you do not have python **3** installed).
```

### What Needs to Update

If for whatever reason the `manufacture.py` script is not working for you, here is all it really does:

1. Replace all instances of `fontawesome` with your font name in
   [`config/fontcustom.yml`](config/fontcustom.yml) file.  Since this name is also used
   to generate C++ code, it is imperative that the fontname satisfies the following
   requirements:

   - They consist of only upper or lower case letters and digits.
   - They start with either an upper or lower case letter.

   So fonts with e.g. a hyphen, or an underscore, or any other special symbols cannot be
   used.  Simply rename the directory underneath `icons/` to satisfy these requirements.

2. It updates three variables at the top of `generate.py`:

   ```py
   # vvv These are updated by ./manufacture.py
   EXPECTED_NUM_ICONS = 929
   FONT_NAME = "fontawesome"
   FONT_LICENSE = "CC-BY-SA 4.0: https://github.com/FortAwesome/Font-Awesome/blob/master/LICENSE.txt"
   # ^^^ These are updated by ./manufacture.py
   ```

## Generate the Font

Now that the `config/fontcustom.yml` has been updated, simply run `rake`.  This is what
it would look like for the `typicons` example.

```console
$ rake
Compiling icons...
      create  .fontcustom-manifest.json
      create  compiled_fonts/typicons
      create  compiled_fonts/typicons/typicons.ttf
              compiled_fonts/typicons/typicons.svg
              compiled_fonts/typicons/typicons.woff
              compiled_fonts/typicons/typicons.eot
              compiled_fonts/typicons/typicons.woff2
      create  compiled_fonts/typicons/_typicons.scss
              compiled_fonts/typicons/typicons.css
              compiled_fonts/typicons/typicons-preview.html
```

One particularly useful file generated here is
`compiled_fonts/typicons/typicons-preview.html`.  You can open that in your browser to
see what everything looks like.  The file that is used for generating the NanoGUI
utilities is `compiled_fonts/typicons/typicons.css`.

# Generate the NanoGUI Utilities

Now that we have the generated files underneath `compiled_fonts/fontname`, we can
proceed to creating the utilities for NanoGUI.

## Generate the Utilities

Assuming you have run `./manufacture.py`, the `./generate.py` script is ready to go.
Otherwise, make sure you have
[updated the three variables at the top](#what-needs-to-update).  As with
`manufacture.py`, the shebang at the top is for Python **3**.  If you do not have Python
**3** installed, run `python generate.py` instead.  With the example `typicons` font:

```console
$ ./generate.py
Found exactly [336] icons, as expected.
```

That's it!

## Use the Utilities

So now we're ready to use all of this stuff.  The files that NanoGUI needs to embed the
font are:

- `fontname.ttf` (which is currently in `compiled_fonts/fontname/fontname.ttf`).  This
  is the true type font that NanoGUI will be embedding directly (via `bin2c`).
- `fontname.h` (which is currently in `nanogui/fontname/fontname.h`).  This is the C++
  header file that will make the embedded icons available for you.
- `constants_fontname.cpp` (which is currently in `nanogui/fontname/constants_fontname.cpp`).
  This is the Python bindings file that make `from nanogui import fontname` available.

NanoGUI expects that all three of these reside in the same directory.  This is done to
make the build interface for specifying custom icon fonts more manageable.  Working with
the `typicons` example, lets first get them all in one directory.

```console
$ mkdir typicons
$ cp compiled_fonts/typicons/typicons.ttf    typicons/
$ cp nanogui/typicons/typicons.h             typicons/
$ cp nanogui/typicons/constants_typicons.cpp typicons/
```

Now, lets assume that your repository using NanoGUI is structured like this:

```console
my_repo/
    CMakeLists.txt
    ext/
        nanogui/  # a git submodule
    resources/    # where we will place these generated resources
```

Then copy the `typicons` folder to `my_repo/resources` (e.g.,
`mkdir /some/path/my_repo/resources` and `cp -r typicons /some/path/my_repo/resources`).
Then the only addition to NanoGUI that you need to make is:

```cmake
list(
  APPEND
  NANOGUI_EXTRA_ICON_RESOURCES
  "${CMAKE_CURRENT_SOURCE_DIR}/resources/typicons/typicons.ttf"
)
```

**before** doing `add_subdirectory(ext/nanogui)`.  The NanoGUI build system will take
care of the rest, including building the python bindings when `NANOGUI_BUILD_PYTHON` is
set to `ON`.

A quick way for you to test is to add the example C++ application.  Supposing you copied
`nanogui/typicons/example_typicons.cpp` to `my_repo/src/example_typicons.cpp`, you can
quickly create a test application to see how the new icon font looks:

```cmake
# ... this is all happening **after** add_subdirectory(ext/nanogui) ...
# Make sure you include ${NANOGUI_EXTRA_INCS}!
include_directories(ext/nanogui/include ${NANOGUI_EXTRA_INCS})
add_executable(example_typicons src/example_typicons.cpp)
target_link_libraries(example_typicons nanogui ${NANOGUI_EXTRA_LIBS})
```

# License

There are two licenses that apply to this repository.  It was designed for use with
[NanoGUI][nanogui], and so it inherits NanoGUI's BSD 3-clause license.  This applies to
all code found in this repository.  This does **not** apply to the hosted example icon
font generated here.

All SVG icons (in the [`icons/fontawesome`](icons/fontawesome) folder), as well as the
generated fonts and utilities under [`compiled_fonts`](compiled_fonts/) are governed by
the [Font Awesome 5 Free License](https://github.com/FortAwesome/Font-Awesome/blob/master/LICENSE.txt).

[nanogui]: https://github.com/wjakob/nanogui
