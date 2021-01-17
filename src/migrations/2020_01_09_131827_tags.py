from orator.migrations import Migration


class Tags(Migration):

    def up(self):
        """
        Run the migrations.
        """
        with self.schema.create('tags') as table:
            table.increments('id')
            table.string('hwid').unique()
            table.string('description')
            table.boolean('is_enabled')
            table.timestamps()
        

    def down(self):
        """
        Revert the migrations.
        """
        self.schema.drop('tags')
        
        