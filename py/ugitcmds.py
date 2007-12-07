import os
import re
import time
import commands
import ugitutils

def git_add (to_add):
	'''Use 'git add' to add files to the index.'''

	if not to_add: return 'ERROR: No files to add.'

	argv = [ 'git', 'add' ]
	for filename in to_add:
		argv.append (ugitutils.shell_quote (filename))

	cmd = ' '.join (argv)
	return 'Running:\t%s\n%s\n%s added successfully' % (
			cmd, commands.getoutput (cmd), ', '.join (to_add) )

def git_add_or_remove (to_process):
	'''Use 'git add' to add files to the index.'''

	if not to_process: return 'ERROR: No files to add or remove.'

	to_add = []
	output = ''

	for filename in to_process:
		if os.path.exists (filename):
			to_add.append (filename)
	
	if to_add:
		output += git_add (to_add) + '\n\n'

	if len(to_add) == len(to_process):
		# to_process only contained unremoved files --
		# short-circuit the removal checks
		return output

	# Process files to add
	argv = [ 'git', 'rm' ]
	for filename in to_process:
		if not os.path.exists (filename):
			argv.append (ugitutils.shell_quote (filename))

	cmd = ' '.join (argv)
	return output + 'Running: %s\n%s' % ( cmd, commands.getoutput (cmd) )

def git_branch():
	'''Returns 'git branch''s output in a list.'''
	return commands.getoutput ('git branch').split ('\n')

def git_commit (msg, amend, commit_all, files):
	'''Creates a git commit.  'commit_all' triggers the -a
	flag to 'git commit.'  'amend' triggers --amend.
	'files' is a list of files to use for commits without -a.'''

	if not msg:
		return 'ERROR: No commit message was provided.'

	# Allow TMPDIR/TMP with a fallback to /tmp
	tmpdir = os.getenv ('TMPDIR', os.getenv ('TMP', '/tmp'))

	# Sure, this is a potential "security risk," but if someone
	# is trying to intercept/re-write commit messages on your system,
	# then you probably have bigger problems to worry about.
	tmpfile = os.path.join (tmpdir,
			'ugit.%s.%s' % ( os.getuid(), time.time() ))

	argv = [ 'git', 'commit', '-F', tmpfile ]

	if amend: argv.append ('--amend')
	
	if commit_all:
		argv.append ('-a')
	else:
		if not files:
			return 'ERROR: No files selected for commit.'

		argv.append ('--')
		for file in files:
			argv.append (ugitutils.shell_quote (file))

	# Create the commit message file
	file = open (tmpfile, 'w')
	file.write (msg)
	file.close()
	
	# Run 'git commit'
	cmd = ' '.join (argv)
	output = commands.getoutput (cmd)
	os.unlink (tmpfile)

	return 'Running:\t%s\n%s' % ( cmd, output )

def git_current_branch():
	'''Parses 'git branch' to find the current branch.'''
	for branch in git_branch():
		if branch.startswith ('* '):
			return branch.lstrip ('* ')
	raise Exception, 'No current branch'

def git_diff (filename, staged=True):
	deleted = False
	argv = [ 'git', 'diff', '--color']
	if staged:
		deleted = not os.path.exists (filename)
		argv.append ('--cached')

	argv.append ('--')
	argv.append (ugitutils.shell_quote (filename))

	diff = commands.getoutput (' '.join (argv))
	diff_lines = diff.split ('\n')

	output = []
	start = False
	del_tag = 'deleted file mode '

	for line in diff_lines:
		if not start and '@@ ' in line and ' @@' in line:
			start = True
		if start or (deleted and del_tag in line):
			output.append (line)
	return '\n'.join (output)

def git_diff_stat ():
	return commands.getoutput ('git diff --color --stat HEAD^')

def git_reset (to_unstage):
	'''Use 'git reset' to unstage files from the index.'''

	if not to_unstage: return 'ERROR: No files to reset.'

	argv = [ 'git', 'reset', '--' ]
	for filename in to_unstage:
		argv.append (ugitutils.shell_quote (filename))

	cmd = ' '.join (argv)
	return 'Running:\t%s\n%s' % ( cmd, commands.getoutput (cmd) )

def git_show_cdup():
	'''Returns a relative path to the git project root.'''
	return commands.getoutput ('git rev-parse --show-cdup')

def git_status():
	'''RETURNS: A tuple of staged, unstaged and untracked files.
	( array(staged), array(unstaged), array(untracked) )'''

	status_lines = commands.getoutput ('git status').split ('\n')

	unstaged_header_seen = False
	untracked_header_seen = False

	modified_header = '# Changed but not updated:'
	modified_regex = re.compile('(#\tmodified:|#\tnew file:|#\tdeleted:)')

	untracked_header = '# Untracked files:'
	untracked_regex = re.compile ('#\t(.+)')

	staged = []
	unstaged = []
	untracked = []

	for status_line in status_lines:
		if untracked_header in status_line:
			untracked_header_seen = True
			continue
		if not untracked_header_seen:
			continue
		match = untracked_regex.match (status_line)
		if match:
			filename = match.group (1)
			untracked.append (filename)

	for status_line in status_lines:
		if modified_header in status_line:
			unstaged_header_seen = True
			continue
		match = modified_regex.match (status_line)
		if match:
			tag = match.group (0)
			filename = status_line.replace (tag, '')
			if unstaged_header_seen:
				unstaged.append (filename.lstrip())
			else:
				staged.append (filename.lstrip())

	return ( staged, unstaged, untracked )
