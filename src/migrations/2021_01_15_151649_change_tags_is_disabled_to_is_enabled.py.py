from orator.migrations import Migration


class ChangeTagsIsDisabledToIsEnabled.py(Migration):

    def up(self):
        """
        Run the migrations.
        """
        with self.schema.table('tags') as table:
            # run ('UPDATE tags SET is_disabled = NOT is_disabled')
            schema.rename('is_disabled', 'is_enabled')
            

    def down(self):
        """
        Revert the migrations.
        """
        with self.schema.table('tags') as table:
            schema.rename('is_enabled', 'is_disabled')
            
