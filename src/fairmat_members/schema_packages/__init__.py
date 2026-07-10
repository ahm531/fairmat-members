from nomad.config.models.plugins import SchemaPackageEntryPoint


class FAIRmatMembersSchemaPackageEntryPoint(SchemaPackageEntryPoint):
    def load(self):
        from fairmat_members.schema_packages.schema_package import m_package

        return m_package


schema_package_entry_point = FAIRmatMembersSchemaPackageEntryPoint(
    name='FAIRmatMembersSchemaPackage',
    description='Schema package for the FAIRmat member directory.',
)
