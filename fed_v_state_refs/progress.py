class Progress:
    def __init__(self, total):
        self.count = 0
        self.total = total
        self.previous_len = 0

    def show(self, message, increment=1):
        percent = '{:2.1%}'.format(self.count / self.total)
        message_len = len(message)
        spaces = ' ' * max(0, self.previous_len - message_len)
        self.previous_len = message_len
        self.count += increment
        message = f'[{percent}] {message} {spaces}'
        print('\r' + message, end="\r")

    def clear(self):
        print('\r' + ' ' * (self.previous_len + 16), end="\r")
