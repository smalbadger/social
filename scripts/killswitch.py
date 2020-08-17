from common.authenticate import ftp
import os


if __name__ == '__main__':



    with open('tmp.txt', 'w') as f:
        ftp.retrlines('RETR social.txt', callback=lambda line: f.write(line + '\n'))

    with open('tmp.txt', 'r') as f:

        lines = f.readlines()

    if lines[0] in ('True', 'True\n'):
        result = input('You are about to turn on the killswitch, are you sure you want to continue (y/n)? ')

        if result != 'y':
            exit()

        lines[0] = 'False\n'
        print()
        print('Killswitch turned ON, any running instances will stop running within a few seconds')
    else:
        lines[0] = 'True\n'
        print('Killswitch disabled, instances can now run normally.')

    with open('tmp.txt', 'w') as f:
        f.writelines(lines)

    with open('tmp.txt', 'rb') as f:
        ftp.storlines('STOR social.txt', f)

    os.remove('tmp.txt')
