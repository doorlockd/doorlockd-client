from orator.migrations import Migration


class AddIsEnabled(Migration):

	def up(self):
		"""
		Run the migrations.
		"""
		with self.schema.table('users') as table:
			# run ('UPDATE tags SET is_enabled = NOT is_disabled')
			table.boolean('is_enabled').default(True)
			
		with self.schema.table('tags') as table:
			# run ('UPDATE tags SET is_enabled = NOT is_disabled')
			table.boolean('is_enabled').default(True)
			

	def down(self):
		"""
		Revert the migrations.
		"""
		with self.schema.table('uses') as table:
			table.drop_column('is_enabled')
		
		with self.schema.table('tags') as table:
			table.drop_column('is_enabled')
		