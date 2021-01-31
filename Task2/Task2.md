# Codebreakers 2020 

## Task 2 - Social Engineering - (Computer Forensicx, Metadata Analysis, Encryption Tools)

### Points: 40

### Description

```
The name of the encrypted file you found implies that it might contain credentials for the journalist's various applications and accounts. Your next task is to find information on the journalist's computer that will allow you to decrypt this file.
```

### Files

home.zip (Same from Task 1)

### Solution

After having located the keychain file, we now what to find a way to decrypt it, running `file` on the file will show us that it is:

```
keychain: GPG symmetrically encrypted data (AES256 cipher)
```

 With this we need to find a password to successfully decrypt it. Looking at the pwHints.txt file I got the following hint

```
keychain: pet name + pet bday
```

Then from there looking at the other various files, inside `Documents/Blog-Articles/blogIntro.txt` I find that his pet cat's name is `Sheba`.

```
Jake here. Welcome to the 'Diary of an Exotic Furry Voyager'. Outside of work, my two favorite things are traveling the world and getting to come home to my favorite furry little friend, and the best friend on the planet, Sheba. This blog is going to account for some of my travels and more importantly, the animals I meet on the way. Hope you enjoy!
```

Inside `Pictures/Pets/shenanigans.jpg` we have what appears to be a birthday party for Sheba, looking at the date we can see that his birthday might be on March 8th.

From this we can create a wordlist of possible passwords to decrypt the file, since we don't know the exact structure of the data or how Sheba may have been capitalized we will need to try several different possibilities. Below is a quick python script I used to generate several possibilities.

```python
name = ["sheba","Sheba","SHEBA"]
dates = ["0803","83","083","803","83","0803","803","083","0308","038","308","38","08/03","08/3","8/03","8/3","03/08","03/8","3/08","3/8"]
fd = open('./wordlist','w')
for y in name:
    for x in dates:
        fd.write(y + str(x) + '\n')
```

Now that we have a possible wordlist we also need a way to test the words against the file, I went with using `gpg2john` to generate a hash that `john` would work against. Using the created hash along with the wordlist told me that the password was `Sheba0308` and the solution to the second task.

