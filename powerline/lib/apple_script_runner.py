# vim:fileencoding=utf-8:noet

def asrun(ascript):
  "Run the given AppleScript and return the standard output and error."
  from subprocess import Popen, PIPE
  osa = Popen(['osascript', '-'],
                         stdin=PIPE,
                         stdout=PIPE)
  return osa.communicate(ascript)[0]

def asquote(astr):
  "Return the AppleScript equivalent of the given string."

  astr = astr.replace('"', '" & quote & "')
  return '"{}"'.format(astr)
