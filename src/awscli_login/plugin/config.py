# Add methods that depend on awscli here

from awscli.customizations.configure.writer import ConfigFileWriter

from ..config import Profile as BaseProfile
from ..util import secure_touch


class Profile(BaseProfile):
    # TODO Add validation...
    def update(self) -> None:
        """ Interactively update the profile. """
        new_values = {}
        writer = ConfigFileWriter()

        for attr, string in self._config_options.items():
            value = getattr(self, attr, self._optional.get(attr))

            prompt = "%s [%s]: " % (string, value)
            value = input(prompt)

            if value:
                new_values[attr] = value

        if new_values:
            if self.name != 'default':
                new_values['__section__'] = self.name

            secure_touch(self.config_file)
            writer.update_config(new_values, self.config_file)
