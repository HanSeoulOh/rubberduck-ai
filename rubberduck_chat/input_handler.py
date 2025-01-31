from typing import Callable

from rubberduck_chat.chat_gpt.chat import GptChat
from rubberduck_chat.chat_gpt.credentials import ask_for_key_input
from rubberduck_chat.configs import *

try:
  import readline
except ImportError:
  try:
    from pyreadline3 import Readline

    readline = Readline()
  except ImportError:
    pass


class Command:
  def __init__(self, trigger: str, action: Callable[[str], None], description: str):
    self.trigger = trigger
    self.trigger_with_space = f'{trigger} '
    self.action = action
    self.description = description


def start_evaluation_loop(gpt_chat: GptChat):
  commands = get_command_triggers(gpt_chat)

  while True:
    try:
      user_input = input('>>>')
      is_command = False

      if user_input.isnumeric() and gpt_chat.has_snippet(int(user_input)) and int(user_input) > 0:
        gpt_chat.copy_snippet(int(user_input))
        continue

      for command in commands:
        if user_input == command.trigger or user_input.startswith(command.trigger_with_space):
          command.action(user_input)
          is_command = True
          continue

      if not is_command:
        gpt_chat.process_prompt(user_input)

    except KeyboardInterrupt:
      exit()


def print_get_help_message():
  help_commands = config_collection.help_command_trigger.get_value().split(config_array_delimiter)

  if len(help_commands) > 0:
    print(f'Type `{help_commands[0]}` for more information')


def process_help_command(gpt_chat: GptChat):
  commands = get_command_triggers(gpt_chat)
  description_to_command_map: dict[str, list[str]] = {}

  for command in commands:
    if command.description in description_to_command_map:
      description_to_command_map[command.description].append(command.trigger)
    else:
      description_to_command_map[command.description] = [command.trigger]

  trigger_description_pairs: list[tuple[str, str]] = []

  for key in description_to_command_map.keys():
    triggers = description_to_command_map[key]
    triggers.sort()
    trigger_description_pairs.append((' '.join(triggers), key))

  trigger_description_pairs.sort(key=lambda trigger_description_pair: trigger_description_pair[0])

  for pair in trigger_description_pairs:
    triggers = pair[0]
    description = pair[1]

    # This is not a good solution, but I'll deal with it later
    triggers_length = len(triggers)
    if triggers_length >= 24:
      print(f'{triggers}\t{description}')
    if triggers_length >= 16:
      print(f'{triggers}\t\t{description}')
    if triggers_length >= 8:
      print(f'{triggers}\t\t\t{description}')
    else:
      print(f'{triggers}\t\t\t\t{description}')


def process_exit_command():
  exit()


def get_command_triggers(gpt_chat: GptChat) -> list[Command]:
  commands: list[Command] = []

  commands += get_command(config_collection.supported_command_cli,
                          lambda user_input: os.system(user_input),
                          'Input is executed on the command line')
  commands += get_command(config_collection.exit_command_trigger,
                          lambda user_input: process_exit_command(),
                          'Exit application')
  commands += get_command(config_collection.help_command_trigger,
                          lambda user_input: process_help_command(gpt_chat),
                          'Print this help message')
  commands += get_command(config_collection.change_session_command_trigger,
                          lambda user_input: gpt_chat.change_session(),
                          'Change chat session')
  commands += get_command(config_collection.print_session_command_trigger,
                          lambda user_input: gpt_chat.print_current_session(),
                          'Print current session')
  commands += get_command(config_collection.new_session_command_trigger,
                          lambda user_input: gpt_chat.create_new_session(),
                          'Create new session')
  commands += get_command(config_collection.update_key_command_trigger,
                          lambda user_input: ask_for_key_input(),
                          'Update OpenAi credential key')

  commands.sort(key=lambda c: len(c.trigger), reverse=True)

  return commands


def get_command(entry: ConfigEntry, create_command_trigger: Callable, description: str) -> list[Command]:
  commands: list[Command] = []
  command_triggers = entry.get_value().split(config_array_delimiter)

  for trigger in command_triggers:
    stripped_trigger = trigger.strip()
    if len(stripped_trigger) > 0:
      commands.append(Command(stripped_trigger, create_command_trigger, description))

  return commands
