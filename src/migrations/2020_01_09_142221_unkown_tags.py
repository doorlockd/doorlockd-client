from orator.migrations import Migration


class UnkownTags(Migration):

	def up(self):
		"""
		Run the migrations.
		"""
		with self.schema.create('unknown_tags') as table:
			table.increments('id')
			table.string('hwid')
			
			table.timestamps()
		

	def down(self):
		"""
		Revert the migrations.
		"""
		self.schema.drop('unknown_tags')
		
		