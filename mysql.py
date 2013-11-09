#!/usr/bin/env python
import sys, os, subprocess, ConfigParser
from datetime import datetime

class Mysql:

    def __init__(self):

        # Get credentials from config file
        config = ConfigParser.ConfigParser()
        config.read("config.yml")
        self.username = config.get('mysql', 'user')
        self.password = config.get('mysql', 'password')
        self.hostname = config.get('mysql', 'host')
        self.backups_directory = config.get('mysql', 'backups_directory')


    def backup(self, database = 'all'):

        # If we did not get a database name we are backing up
        # all the databases on the server
        if database == 'all':

            # Get a list of dbs to backup
            databases = self.__build_db_list(['information_schema', 'performance_schema'])

            # Backup all database in our list
            for db in databases:
                self.__backup_database(db)

        else:
            # We are backing up a single database
            self.__backup_database(db)



    def __remove_file(self, file_name):

        # If the file exists delete it
        try:
            os.remove(file_name)
        except OSError:
            pass


    def __cmd(self, command):

        # Create a subprcess and execute the command we are given
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, errors = p.communicate()
        return (output, errors, p.returncode)


    def __build_db_list(self, exclude = []):

        command = "mysql -u %s --password=%s -h %s --silent -N -e 'show databases'" % (self.username, self.password, self.hostname)
        response = self.__cmd(command)

        # If something bad happened bail out and show it
        if response[2] > 0:
            print response[1]
            sys.exit(1)

        # Clean up output and build our db list
        dbs = response[0].strip().split('\n')

        # Extract all the databases in our exclude list...if they dont
        # exist in the list dont throw an error
        for db in exclude:
            try:
                dbs.remove(db)
            except ValueError:
                continue

        return dbs


    def __backup_database(self, database):

        # Add date of the backup to the backup name
        date = datetime.now().strftime('%Y%m%d')
        backup_name =  "%s%s_%s.sql" % (self.backups_directory, database, date)

        # Mysql dump options
        options = "--extended-insert --lock-tables --allow-keywords --add-drop-table --net_buffer_length=7M"

        # We need two versions of the commands...one with locks and one without for dealing with large databases
        # that cause us to exhaust our file descriptors
        backup_with_locks = "mysqldump -u %s --password=%s -h%s %s %s | \
                            gzip -c > %s.gz; (exit ${PIPESTATUS[0]})" % (self.username, self.password, self.hostname,
                                                                         options, database, backup_name)
        backup_without_locks = "mysqldump -u %s --password=%s -h%s %s %s | \
                                gzip -c > %s.gz; (exit ${PIPESTATUS[0]})" % (self.username, self.password, self.hostname,
                                                                             options + " --lock-tables=false", database,
                                                                             backup_name)

        # Before we do the backup make sure the backup directory is present if one is set.
        # Otherwise we will be dumping to the current working directory
        if self.backups_directory:
            try:
                eos.makedirs(self.backups_directory)
            except OSError:
                pass

        # Execute our backup
        response = self.__cmd(backup_with_locks)

        # Special case to handle running out of file descriptors for large databases
        if response[2] == 2:

            # Clean up any partial files we created in this retry process
            self.__remove_file(backup_name)

            # Execute the backup again without locks this time
            response = self.__cmd(backup_without_locks)

        # At this point we have failed lets say something
        if response[2] > 0:
            print 'Failed to backup database: ', database

            # Clean up any potential partial files generated during error
            self.__remove_file(backup_name)
