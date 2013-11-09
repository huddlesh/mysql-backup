## Mysql backup

Small python class for dumping and compressing databases in mysql


### Usage

* copy config.yml-dist to config.yml and set appopriate values 
* example config:

        [mysql]
        user: myuser
        password: mypassword
        host: mysqlhost
        backups_directory: /path/toplace/mybackups

* note: if backups_directory is not specified the current working directory is used       
* example usage:

        from mysql import Mysql
        # Create new Mysql object
        m = Mysql()
        # Dump all databases
        m.backup()
        # Dump a specific database
        m.backup(database_name)
* file output will be compressed and in the form dbname_yyymmdd.sql.gz in the directory specified by backups_directory 



