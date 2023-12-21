#
# This is a .tape file for vhs, which will turn it into a gif
# run it like:
#
# $ vhs commandline.tape
#

Output commandline.gif

Set Framerate 15

Set FontFamily "MesloLGL Nerd Font Mono"
Set FontSize 14

Set Width 933
Set Margin 20
Set Padding 0

Set TypingSpeed 60ms

Type "tomcat-manager --user=ace --password=newenglandclamchowder http://localhost:8080/manager deploy local tests/war/sample.war /sampleapp" Sleep 200ms Enter
Sleep 3s
Type "echo $?" Sleep 200ms Enter
Sleep 2s
