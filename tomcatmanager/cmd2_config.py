#
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007 Jared Crapo
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import os
import configparser
import appdirs


class Cmd2Config():
    """
    Mixin for Cmd2 which adds configuration file support for settings.
    
    This mixin provides the following additional capabilities to any Cmd2
    based application:
    
    - on startup, load settings from configuration file (in INI format)
    - new 'config' command which launches editor on the config file
    - new 'set' command  (overrides Cmd2) which allows you to change settings
      in INI format
    - new 'show' command (overrides Cmd2) which shows the settings in INI
      format
    - calls _onchange_{setting}(old,new) after a setting changes value
    - makes self.appdirs available, see https://github.com/ActiveState/appdirs
    - makes self.config available, a ConfigParser object of the configuration file
    
    We want the methods in this class to override those present in Cmd2.Cmd, so you
    must define your parent class with Cmd2Config before Cmd2.Cmd:
    
        class MyApp(Cmd2Config, cmd2.Cmd):
    
    In your initializer, you have to initialize cmd2.Cmd before Cmd2Config. You
    also need to define two attributes, `app_name` and `app_author`. These are
    used to determine the platform-specific directory where your configuration
    file should reside.
    
        def __init__(self, prog_name):

            self.app_name = 'MyApp'
            self.app_author = 'Acme'
    
            cmd2.Cmd.__init__(self)
            Cmd2Config.__init__(self)
    
    If you don't define `app_name` and `app_author`, then all these fancy new
    features will be disabled.
    
    You should set a value for all setting attributes in code before calling
    the initializer for this class:
    
        self.timing = 10
        Cmd2Config.__init__(self)
    
    Settings read from the configuration file are all strings. This class will
    coerce the strings into whatever type is contained in the attribute for
    that setting. If your setting attribute is None, then config will assume
    you wanted a string.
    
    This mixin makes a configuration item from configparser available at self.config, you
    can use this to get any other configuration data you want/need from the user specified
    config file.
    """

    # Possible boolean values
    BOOLEAN_VALUES = {'1': True, 'yes': True,  'y': True,   'true': True,   'on': True,
                      '0': False, 'no': False, 'n': False, 'false': False, 'off': False}

    def __init__(self):
        self.appdirs = None
        try:
            if self.app_name and self.app_author:
                self.appdirs = appdirs.AppDirs(self.app_name, self.app_author)
        except AttributeError:
            pass
        self.load_config()

    ###
    #
    # user accessible configuration commands
    #
    ###
    def do_config(self, args):
        """show the location of the config file"""
        if len(args.split()) == 1:
            action = args.split()[0]
            if action == 'file':
                self.pout(self._configfile)
                self.exit_code = self.exit_codes.success
            elif action == 'edit':
                self.config_edit()
            else:
                self.help_config()
                self.exit_code = self.exit_codes.error
        else:
            self.help_config()
            self.exit_code = self.exit_codes.error

    def config_edit(self):
        """do the 'config edit' command"""
        if not self.editor:
            self.perr("No editor. Use 'set editor={path}' to specify one.")
            self.exit_code = self.exit_codes.error
            return
        
        # ensure the configuration directory exists
        configdir = os.path.dirname(self.config_file)
        if not os.path.exists(configdir):
            os.makedirs(configdir)

        # go edit the file
        cmd = '"{}" "{}"'.format(self.editor, self.config_file)
        self.pdebug("Executing '{}'...".format(cmd))
        os.system(cmd)
        
        # read it back in and apply it
        self.pout('Reloading configuration...')
        self.load_config()
        self.exit_code = self.exit_codes.success

    def help_config(self):
        self.exit_code = self.exit_codes.success
        self.pout("""Usage: config {action}

Manage the user configuration file.

action is one of the following:
  
  file  show the location of the user configuration file
  edit  edit the user configuration file""")

    ###
    #
    # user accessable settings commands
    #
    ###
    def do_show(self, args):
        if len(args.split()) > 1:
            self.help_show()
            self.exit_code = self.exit_codes.error
            return

        param = args.strip().lower()
        result = {}
        maxlen = 0
        for setting in self.settable:
            if (not param) or (setting == param):
                val = str(getattr(self, setting))
                result[setting] = '{}={}'.format(setting, self._pythonize(val))
                maxlen = max(maxlen, len(result[setting]))
        # make a little extra space
        maxlen += 1
        if result:
            for setting in sorted(result):
                self.pout('{} # {}'.format(result[setting].ljust(maxlen), self.settable[setting]))
            self.exit_code = self.exit_codes.success
        else:
            self.perr("'{}' is not a valid setting.".format(param_name))
            self.exit_code = self.exit_codes.error

    def help_show(self):
        self.exit_code = self.exit_codes.success
        self.pout("""Usage: show [setting]

Show one or more settings and their values.

[setting]  Optional name of the setting to show the value for. If omitted
           show the values of all settings.""")

    def do_set(self, args):
        if args:
            config = EvaluatingConfigParser()
            setting_string = "[settings]\n{}".format(args)
            try:
                config.read_string(setting_string)
            except configparser.ParsingError as err:
                self.perr(str(err))
                self.pout('')
                self.help_set()
                self.exit_code = self.exit_codes.error
                return
            for param_name in config['settings']:
                if param_name in self.settable:
                    self._change_setting(param_name, config['settings'][param_name])
                    self.exit_code = self.exit_codes.success
                else:
                    self.perr("'{}' is not a valid setting".format(param_name))
                    self.exit_code = self.exit_codes.error
        else:
            self.do_show(args)

    def help_set(self):
        self.exit_code = self.exit_codes.success
        self.pout("""Usage: set {setting}={value}

Change a setting.

  setting  Any one of the valid settings. Use 'show' to see a list of valid
           settings.
  value    The value for the setting.
""")

    ###
    #
    # other properties/attributes and methods available to our subclasses
    #
    ###
    @property
    def config_file(self):
        f = None
        try:
            if self.appdirs and self.app_name:
                filename = self.app_name + '.ini'
                return os.path.join(self.appdirs.user_config_dir, filename)
        except AttributeError:
            pass

    def load_config(self):
        """
        Find and parse the user config file and set self.config        
        """
        config = None
        if self.config_file is not None:
            config = EvaluatingConfigParser()
            try:
                with open(self.config_file, 'r') as f:
                    config.read_file(f)
            except:
                pass
        try:
            settings = config['settings']
            for key in settings:
                self._change_setting(key, settings[key])
        except KeyError:
            pass
        except ValueError:
            pass
        self.config = config

    def convert_to_boolean(self, value):
        """Return a boolean value translating from other types if necessary.
        """
        if type(value) == bool:
            return value
        else:
            if str(value).lower() not in self.BOOLEAN_VALUES:
                raise ValueError('Not a boolean: {}'.format(value))
            return self.BOOLEAN_VALUES[value.lower()]

    ###
    #
    # private methods
    #
    ### 
    def _change_setting(self, param_name, val):
        """internal method to change a setting
        
        param_name must be in settable or this method with throw a ValueError
        some parameters only accept boolean values, if you pass something that can't
        be converted to a boolean, throw a ValueError
        
        Call _onchange_{param_name}(old, new) after the setting changes value
        """
        if param_name in self.settable:
            current_val = getattr(self, param_name)
            type_ = type(current_val)
            if type_ == bool:
                val = self.convert_to_boolean(val)
            elif type_ == int:
                val = int(val)
            setattr(self, param_name, val)
            if current_val != val:
                try:
                    onchange_hook = getattr(self, '_onchange_{}'.format(param_name))
                    onchange_hook(old=current_val, new=val)
                except AttributeError:
                    pass
        else:
            raise ValueError

    def _pythonize(self, value):
        """turn value into something the python interpreter can parse
        
        we are going to turn val into pval such that

            val = ast.literal_eval(pval)
        
        This isn't quite true, because if there are no spaces or quote marks in value, then
        
            pval = val
        """
        sq = "'"
        dq = '"'
        if (sq in value) and (dq in value):
            # use sq as the outer quote, which means we have to
            # backslash all the other sq in the string
            value = value.replace(sq, '\\'+sq)
            return "'{}'".format(value)
        elif sq in value:
            return '"{}"'.format(value)
        elif dq in value:
            return "'{}'".format(value)
        elif ' ' in value:
            return "'{}'".format(value)
        else:
            return value


import ast
class EvaluatingConfigParser(configparser.ConfigParser):
    def get(self, section, option, **kwargs):
        val = super().get(section, option, **kwargs)
        if "'" in val or '"' in val:
            try:
                val = ast.literal_eval(val)
            except:
                pass
        return val
