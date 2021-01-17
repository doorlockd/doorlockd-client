from orator.migrations import Migration


class Users(Migration):

    def up(self):
        """
        Run the migrations.
        """
        with self.schema.create('users') as table:
            table.increments('id')            
            table.string('email').unique()
            table.string('password_hash')
            table.boolean('is_enabled')
            table.timestamps()        
        
    def down(self):
        """
        Revert the migrations.
        """
        self.schema.drop('users')
        
