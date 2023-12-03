Themes
======

When a theme is set, ``tomcat-manager`` displays colored output using the styles
defined in theme. By default, no theme is applied; all output is displayed using the
default style of your terminal emulator. See https://no-color.org for an explanation
of why this is the best approach.

``tomcat-manager`` comes with several built-in themes which use can use. Built-in
themes can not be edited or modified. You can create your own themes, either from
scratch or by cloning a built-in theme. If connected to the internet, you can view a
gallery of themes available online, and install any of them computer. Once installed,
they can be applied and modified to your liking.

A theme is defined in a file using the `TOML <https://toml.io/en/>`_ format. The file
contains a set of scope definitions, and the style to use when rendering each scope.
Here's a simple example showing several scopes and their associated styles:

.. code-block:: toml

    [tm]
    error =  "#d70000"
    status =  "#00afff"

    [tm.help]
    category =  "gold1"
    border = "gold1"

For convenience, we use the `table <https://toml.io/en/v1.0.0#table>`_ features of
TOML. Those same four scopes could also be defined as:

.. code-block:: toml

    tm.error = "#d70000"
    tm.status =  "#00afff"
    tm.help.category =  "gold1"
    tm.help.border = "gold1"

All scopes and a description of how they are used are listed in
`Theme Scopes`_. A style specifies colors and attributes (like bold or italic)
to use when rendering the scope. See `Styles`_ for more information


Listing Themes
--------------

The following command displays all themes known to ``tomcat-manager``:

.. code-block:: text

    tomcat-manager> theme list
    Gallery Themes
    ────────────────────────────────────────────────────────────────────────
    monokai           monokai theme using color scheme from https://monokai.pro/
    solarized-dark    dark theme using solarized color scheme from
                        https://ethanschoonover.com/solarized/
    solarized-light   light theme using solarized color scheme from
                        https://ethanschoonover.com/solarized/

    User Themes
    ────────────────────────────────────────────────────────────────────────
    default-light*   tomcat-manager default theme for use on light backgrounds
    default-dark*    tomcat-manager default theme for use on dark backgrounds

    '*' indicates a read-only built-in theme.
    Make your own copy of a built-in or gallery theme with 'theme clone'.
    You can then edit your copy of the theme with 'theme edit'.

The themes are divided into two sections. Gallery themes are retrieved from a website
and must be installed locally before they can be used. User themes have already been
installed and are available for use. Some themes are included with the
``tomcat-manager`` distribution, and are marked with an asterisk to indicate they are
built-in. These themes can be used and cloned, but may not be modified. You can clone
one of these built-in themes and give it the same name, if you do so, the asterisk will
disappear and you will be able to edit the theme.


Setting a Theme
---------------

When ``tomcat-manager`` is launched, it checks the following items in the order given
until it finds a theme setting. If no theme is set by any of these items, then no
theme is applied.

- ``--theme`` command line option
- ``TOMCATMANAGER_THEME`` environment variable
- the ``theme`` setting in the :doc:`configuration file <configfile>`

If you have a setting in your config file to set the theme:

.. code-block:: toml

    [settings]
    theme = "default-light"

And you invoke ``tomcat-manager`` using the following:

.. code-block:: bash

    $ tomcat-manager --theme default-dark

The theme will be set to ``default-dark``, because the command line option is checked
first, and if found, all other mechanisms to set the theme are ignored.

This approach has been implemented because it offers great flexibility and makes
integration with other shell tools and environments easy.

Once ``tomcat-manager`` is running, you can apply a new theme by by changing the
:ref:`theme setting <interactive/settings:theme>` to the name of the theme you want to
load. Any future output will now be generated using the styles specified in the loaded
theme.

.. code-block:: text

    tomcat-manager> set theme = "default-dark"

If you don't want to use a theme, type:

.. code-block:: text

    tomcat-manager> set theme = ""

``tomcat-manager`` comes with built-in themes which can not be changed. If you create
your own theme with the same name as one of the built-in themes your theme will be
loaded instead of the built-in theme with the same name.


Creating a User Theme
----------------------

There are four ways to create a user theme:

- clone a gallery theme
- clone a built-in theme
- create a new theme from scratch
- copy a theme file from another computer

Once you have a user theme, you can freely :ref:`edit <interactive/themes:Editing a
Theme>` it.

Use the following command to clone a gallery or built-in theme to a user theme:

.. code-block:: text

    tomcat-manager> theme clone solarized-dark

You can use ``theme list`` to verify that the theme has been successfully cloned.

To create a new user theme from scratch, use:

.. code-block:: text

    tomcat-manager> theme create my-new-theme

A new theme file will be created from a template which includes all available scopes.
You can then :ref:`edit <interactive/themes:Editing a Theme>` the theme, adding
:ref:`interactive/themes:Styles` to the scopes to achieve the desired color output.

Any user theme file can be copied to another computer. Place it in the :ref:`local
theme directory <interactive/themes:Location of Theme Files>` to make it avaialble to
``tomcat-manager``.


Location of Theme Files
-----------------------

User themes are stored in a configuration directory. The location of this
directory is different depending on the operating system. You can see the exact
directory for your setup by typing the following from your operating system shell
prompt:

.. code-block:: bash

    $ tomcat-manager --theme-dir
    /Users/kotfu/Library/Application Support/tomcat-manager/themes

You can get the same information from within ``tomcat-manager`` by typing:

.. code-block:: text

    tomcat-manager> theme dir
    /Users/kotfu/Library/Application Support/tomcat-manager/themes

When you clone a theme from the gallery, or create a new theme, it is placed into this
directory. Any actions you take on files in this directory (deleting, renaming,
copying, etc) are immediately recognized in the ``tomcat-manager`` tool.

Theme files from this directory can be shared or copied to another computer.


Editing a Theme
---------------

Gallery themes are not available to edit. They can be cloned to your local machine,
and then freely edited. Built-in themes are local, but they are read-only. See
:ref:`interactive/themes:Listing Themes` above to learn how to display all available
themes.

Edit a user theme by:

.. code-block:: text

    tomcat-manager> theme edit [name]

replacing ``[name]`` with the name of the user theme. The theme file
will open in your editor of choice (see :ref:`interactive/settings:editor`
setting). If you edit the currently loaded theme, it will be reloaded after
the editor exits.

See :ref:`interactive/themes:Theme Scopes` and :ref:`interactive/themes:Styles` for
documentation on what to put in a theme file to create the desired output.


Deleting a Theme
----------------

You can delete any user theme (except for the read-only build-in themes):

.. code-block:: text

    tomcat-manager> theme delete [name]

replacing ``[name]`` with the name of the user theme you would like to delete. You
will be prompted to confirm the deletion unless you provide the ``-f`` option.


Theme Scopes
------------

Here's a list of all the scopes which ``tomcat-manager`` can use when defined in a
theme. In this example, all scopes are set to a style of ``default``, which displays
the scope in the default foreground and background color of your terminal emulator.

If a theme contains unknown scopes, they will be ignored.

.. code-block:: toml

    # These scopes are applied to output generated by many commands.
    [tm]
    # error messages
    error =  "default"
    # status messages
    status =  "default"
    # progress animations for long-running commands (like connect or list)
    animation = "default"


    # When run with no arguments, the 'help' command shows a categorized list
    # of all the available commands. These scopes control the display of that
    # categorized list.
    [tm.help]
    # the name of a category or grouping of commands
    category =  "default"
    # the border line below the category  name
    border = "default"
    # the name of the command shown in the first column
    command =  "default"
    # arguments to the 'help' command
    args = "default"


    # These scopes are used when displaying help or usage for a specific command
    # i.e. when typing 'connect -h' or 'help connect'.
    [tm.usage]
    # name of the command
    prog =  "default"
    # groups of arguments, ie 'positional arguments:', and 'options:'
    groups =  "default"
    # the positional arguments and options
    args =  "default"
    # values for options, ie KEY is the metavar in '--key KEY'
    metavar =  "default"
    # the description of positional arguments and options
    help =  "default"
    # command descriptions, epilogs, and other text
    text =  "default"
    # syntax or references inline in other text
    syntax =  "default"


    # Used by the 'list' command which shows information about each
    # application deployed in the Tomcat server.
    [tm.list]
    # column headers in the table of displaye dinformation
    header =  "default"
    # the border line underneath the column headers
    border =  "default"


    # When showing details of an app deployed in a tomcat server,
    # like by the list command, use these scopes for attributes
    # of each application.
    [tm.app]
    # if the application is running, show the word 'running' in this style
    running =  "default"
    # if the application is stopped, show the word 'stopped' in this style
    stopped =  "default"
    # show the number of active sessions in this style
    sessions =  "default"

    # These scopes are used by the 'settings' command to show the various
    # program settings.
    [tm.setting]
    # name of the setting
    name =  "default"
    # the equals sign separating the setting from it's value
    equals =  "default"
    # the comment containing the description of the setting
    comment =  "default"
    # values which are strings, like 'prompt'
    string =  "default"
    # values which are boolean, like 'debug' and 'echo
    bool =  "default"
    # values which are integers, we have no settings with integer values
    # but have added it to all themes just in case
    int =  "default"
    # values which are floats, like 'timeout'
    float =  "default"


    # These scopes used by the 'theme list' command to show all available themes
    [tm.theme]
    # the category or group name of a set of themes
    category = "default"
    # the border line below the category name
    border = "default"


Styles
------

You can set a style for each theme scope. If you set the style
to ``default`` or if the scope is not present in the theme file,
no codes will be sent to your terminal emulator to style that scope.
That means that text in that scope will be displayed in the default
colors of your terminal emulator.

A style can specify colors and attributes (like bold or italic). Ancient terminals are
monochrome, really old terminals could display 16 colors, old terminals can display
256 colors, most modern terminals can display 16.7 million colors.

Specify a color using any of the following:

.. list-table::
  :widths: 40 60
  :header-rows: 1

  * - Color Specification
    - Description
  * - ``#8700af``
    - CSS-style hex notation
  * - ``rgb(135,0,175)``
    - RGB form using three integers
  * - ``dark_magenta``
    - color names
  * - ``color(91)``
    - color numbers

Color names and numbers are shown at
https://rich.readthedocs.io/en/stable/appendix/colors.html

All of the above forms produce the exact same color.

When only one color is specified in the style, it will set the foreground color. To
set the background color, preceed the color with the word "on".

- ``white on rgb(135,0,75)``
- ``#ffffff on dark_magenta``

As shown above, you can mix and match the color specification format in a single style.
For consistency, I recommend that you pick one color specification format and use it.
The built-in themes use color names for two reasons:

- The color names limit you to the 256 color space, making the theme work on a larger
  variety of terminal emulators
- For those of us who can't intuitively translate hex into colors, the names give you
  some idea of what the color is.

Specify additional text attributes by adding additional words to the style:

- ``#ffffff on #8700af bold strike``
- ``color(91) underline``

The most useful text attributes are:

.. list-table::
  :widths: 40 60
  :header-rows: 1

  * - Attribute
    - Description
  * - ``bold``
    - bold or heavy text
  * - ``italic``
    - italic text (not supported on Windows)
  * - ``strike``
    - text with a strikethrough line
  * - ``underline``
    - underlined text

For more examples and additional documentation on styles, see
https://rich.readthedocs.io/en/stable/style.html
