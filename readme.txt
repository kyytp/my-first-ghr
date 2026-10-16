This is the start of a project
-
there is no direction or timeline 
-
Tips that covers Terminal, Git, nano, and GitHub on macOS.

## 1. Terminal basics

| Command | Meaning |
|---|---|
| `pwd` | Shows the current folder |
| `ls` | Lists files in the folder |
| `ls -a` | Lists files, including hidden files |
| `cd name` | Opens a folder |
| `cd ..` | Goes up one folder |
| `cd ~` | Goes to the Home folder |
| `mkdir name` | Creates a folder |
| `touch name` | Creates an empty file |
| `cat name` | Shows the text in a file |
| `open .` | Opens the current folder in Finder |
| `clear` | Clears the screen |
| `rm name` | Deletes a file. This cannot be undone. |

### Keys

- **Tab**: completes a file or folder name.
- **Up arrow**: shows the previous command.
- **Control + C**: stops a running command.
- **Command + K**: clears the screen.
- **q**: leaves a help page, such as `man ls`.

### Rules

- Check the name before you run `rm`.
- Use quotes for names with spaces: `cd "My Folder"`.
- Names are case-sensitive: `Notes.txt` and `notes.txt` are different files.

## 2. nano (text editor)

Open a file:

```
nano filename
```

| Keys | Action |
|---|---|
| **Control + O**, then **Return** | Save |
| **Control + X** | Exit |
| **Control + W** | Search |
| **Control + K** | Cut the current line |
| **Control + U** | Paste the cut line |
| **Control + G** | Show the help page |

## 3. Git basics

| Command | Meaning |
|---|---|
| `git status` | Shows changed, new, and deleted files |
| `git add file` | Prepares a file to be saved |
| `git add .` | Prepares all changes in the folder |
| `git commit -m "Message"` | Saves a snapshot with a short note |
| `git log` | Shows past snapshots. Press **q** to leave. |
| `git diff` | Shows the exact changes that are not yet saved |
| `git push` | Sends saved snapshots to GitHub |
| `git pull` | Gets new changes from GitHub |
| `git branch name` | Creates a new line of work |
| `git switch name` | Moves to another line of work |

### Daily routine

1. `cd my-first-project`
2. `git status`
3. `git add .`
4. `git commit -m "Describe the change"`
5. `git push`

### Good commit messages

- Write short messages in the present tense, such as `Add setup notes`.
- Make one commit for one change.

## 4. .gitignore

A `.gitignore` file lists files that Git must not track.

Common lines for a Mac:

```
.DS_Store
.env
*.log
```

- A file that Git already tracks stays tracked. To stop tracking it but keep it on your Mac, type: `git rm --cached filename`
- Check the result with `git status`.

## 5. GitHub tips

- Use a **personal access token** or an **SSH key** to prove your identity.
- Create a README on GitHub for each repository. It explains the project.
- Use **issues** to track tasks and problems.
- Use **pull requests** to propose changes.
- Public repositories can be seen by anyone. Do not store passwords or keys in them.

## 6. Troubleshooting

| Message | What to do |
|---|---|
| `command not found` | Check the spelling of the command |
| `No such file or directory` | Check the folder name with `ls` |
| `pathspec did not match` | Check the file name with `git status` |
| `Authentication failed` | Create a new token and use it at the Password prompt |
| `Permission denied` | Check your account access to the repository |

## 7. Practice

1. Create a folder with `mkdir practice` and enter it with `cd practice`.
2. Create a file with `touch notes.txt`.
3. Write a line in the file with `nano notes.txt`. Save and exit.
4. Run `git status`, `git add notes.txt`, and `git commit -m "Add notes"`.
5. Run `git push` and check GitHub.
