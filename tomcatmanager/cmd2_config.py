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
    Mixin for Cmd2 which provides the following functionality:
    
    - new 'set' command
    - new 'show' command
    - load settings from a config file
    
    We want the methods in this class to override those present in Cmd2.Cmd, so you
    must define your parent class with Cmd2Config before Cmd2.Cmd:
    
        class InteractiveTomcatManager(Cmd2Config, cmd2.Cmd):
    
    In your initializer, you have to initialier cmd2.Cmd before Cmd2Config, like this:
    
        def __init__(self, prog_name):

            cmd2.Cmd.__init__(self)
            Cmd2Config.__init__(self, prog_name)
    
    You also need to pass in the program name to the initializer, which will be used
    to determine the location and name of the config file.
    
    If you have default configuration settings you want to use, set them before calling
    the initializer for this class:
    
        self.config_defaults = {
            'settings': {
                'prompt': prog_name + '>',
            }
        }
        Cmd2Config.__init__(self, prog_name)
    
    This mixin makes a configuration item from configparser available at self.config, you
    can use this to get any other configuration data you want/need from the user specified
    config file.
    """

    # Possible boolean values
    BOOLEAN_STATES = {'1': True, 'yes': True,  'y': True,   'true': True,   'on': True,
                      '0': False, 'no': False, 'n': False, 'false': False, 'off': False}

    def __init__(self, prog_name):

        self.prog_name=prog_name

        if not self.config_defaults:
            self.config_defaults = {}
        
        # read in the user configuration file
        self.config = self._load_config()
        self._apply_config()

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
        configdir = os.path.dirname(self._configfile)
        if not os.path.exists(configdir):
            os.makedirs(configdir)

        # go edit the file
        cmd = '{} "{}"'.format(self.editor, self._configfile)
        self.pdebug("Executing '{}'...".format(cmd))
        os.system(cmd)
        
        # read it back in and apply it
        self.pout('Reloading configuration...')
        self.config = self._load_config()
        self._apply_config()
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
            self.exit_code = self.exit_codes.usage

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
    # private methods
    #
    ###
    @property
    def _configfile(self):
        dirs = appdirs.AppDirs(self.prog_name, self.prog_name)
        filename = self.prog_name + '.ini'
        return os.path.join(dirs.user_config_dir, filename)
        
    def _load_config(self):
        """
        Find and parse the user config file and make it available
        as self.config
        
        This starts with the defaults and overrides them with values
        read from the config file.
        """
        config = EvaluatingConfigParser()
        # load the defaults
        config.read_dict(self.config_defaults)
        
        try:
            with open(self._configfile, 'r') as f:
                config.read_file(f)
        except:
            pass
        return config

    def _apply_config(self):
        """apply the configuration to ourself"""
        # settings will always exist because we put default values
        # there in _get_config()
        settings = self.config['settings']
        for key in settings:
            try:
                self._change_setting(key, settings[key])
            except ValueError:
                pass

    def _change_setting(self, param_name, val):
        """internal method to change a setting
        
        param_name must be in settable or this method with throw a ValueError
        some parameters only accept boolean values, if you pass something that can't
        be converted to a boolean, throw a ValueError
        """
        if param_name in self.settable:
            current_val = getattr(self, param_name)
            typ = type(current_val)
            if typ == bool:
                val = self._convert_to_boolean(val)
            setattr(self, param_name, val)
            if current_val != val:
                try:
                    onchange_hook = getattr(self, '_onchange_%s' % param_name)
                    onchange_hook(old=current_val, new=val)
                except AttributeError:
                    pass
        else:
            raise ValueError

    def _convert_to_boolean(self, value):
        """Return a boolean value translating from other types if necessary.
        """
        if value.lower() not in self.BOOLEAN_STATES:
            raise ValueError('Not a boolean: {}'.format(value))
        return self.BOOLEAN_STATES[value.lower()]

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
