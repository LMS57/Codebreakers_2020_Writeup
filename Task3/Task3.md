# Codebreakers 2020 

## Task 3 - Social Engineering - (Computer Forensics, Metadata Analysis, Encryption Tools)

### Points: 150

### Description

```
Good news -- the decrypted key file includes the journalist's password for the Stepinator app. A Stepinator is a wearable fitness device that tracks the number of steps a user walks. Tell us the associated username and password for that account. We might be able to use data from that account to track the journalist's location!
```

### Files

home.zip (Same from Task 1 & 2)

### Solution

With the password of `Sheba0308` from the last challenge we can now decrypt the gpg file with the following command:

```
gpg --cipher-algo AES256 -d -o decrypted keychain
```

From the decrypted file we can find that it is an SQLite database

```
decrypted: SQLite 3.x database, last written using SQLite version 3027002
```

Using `sqlite3` we can load the database and dump all the data within.

```sqlite
JakeBucks261# sqlite3 ./decrypted
SQLite version 3.33.0 2020-08-14 13:23:32
Enter ".help" for usage hints.
sqlite> .dump
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE services(
								id integer PRIMARY KEY, 
								service text NOT NULL,
								keyused integer,
								keyexpired integer);
INSERT INTO services VALUES(1,'email',1,0);
INSERT INTO services VALUES(2,'bank',1,0);
INSERT INTO services VALUES(3,'blog',1,0);
INSERT INTO services VALUES(4,'work server',1,0);
INSERT INTO services VALUES(5,'music',1,0);
INSERT INTO services VALUES(6,'login',1,0);
INSERT INTO services VALUES(7,'house alarm',1,0);
INSERT INTO services VALUES(8,'stepinator',1,0);
CREATE TABLE passwords(
								id integer PRIMARY KEY,
								service integer NOT NULL,
								username text,
								pwd text NOT NULL,
								valid integer NOT NULL,
								FOREIGN KEY (service) REFERENCES services (id));
INSERT INTO passwords VALUES(1,1,'Jake_Bucks','<~<+oi@Df9`=7;PJ7ARfX42_d#~>',1);
INSERT INTO passwords VALUES(2,2,'JBucks','<~0ekFB;eT`O@/~>',1);
INSERT INTO passwords VALUES(3,3,'Sheba-Jake','<~6Z7!_Ao)C0ATC^_AR]''~>',1);
INSERT INTO passwords VALUES(4,4,'JBucks0313','<~;eT`O@50Jl2Z~>',1);
INSERT INTO passwords VALUES(5,5,'Jake_Bucks','<~0K(XB<H*"nA7\/IGA]cVCLm~>',1);
INSERT INTO passwords VALUES(6,6,'JakeBucks261','<~0JkID6?Qf~>',1);
INSERT INTO passwords VALUES(7,7,'157930313','<~<H*"nA7\/IGA]cVCLm~>',1);
INSERT INTO passwords VALUES(8,8,'Sheba_Bucks_0308','<~6Z7!_Ao)C0ATC^_AR](&0et[A2DI#~>',1);
COMMIT;
sqlite> 
```

From the above dump we can see that there is a relation ship between the service.id and password.id fields, so the index 8 stepinator account corresponds to the username `Sheba_Bucks_0308` and the password `<~6Z7!_Ao)C0ATC^_AR](&0et[A2DI#~>`. At first you may think that this is a secure password with distinct characters and symbols, but upon further inspection you may notice the `<-` and `->` leading and trailing each password respectively. This is a clue to that the passwords are encoded with the same method. The encoding done here is base85 and decoding it gives the password `CornflowerSheba11270614`