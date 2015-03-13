import boothlarge
boothlarge.STORE_DIR = 'large'
b = boothlarge.BoothView()

LINES = """Booth2389-0005
Booth2389-0006
Booth2389-0007
Booth2389-0008
Booth2389-0009
Booth2389-0021
Booth2389-0026
Booth2389-0029
Booth3235-0005
Booth3235-0010
Booth3235-0014
Booth3235-0015
Booth3235-0016
Booth3235-0017
Booth3235-0018
Booth3235-0019
Booth3235-0021
Booth3235-0023
Booth3235-0024
Booth3235-0025
Booth3235-0026
Booth3235-0027
Booth3235-0028
Booth3235-0029
Booth3235-0030
Booth3235-0031
Booth3235-0033
Booth3235-0036
Booth3235-0037
Booth3235-0038
Booth3235-0040
Booth3235-0053
Booth3235-0056
Booth3235-0057
Booth3235-0058
Booth3235-0059
Booth3235-0061
Booth3235-0065
Booth3235-0066
Booth3235-0067
Booth3235-0068
Booth3235-0070
Booth3235-0071
Booth3235-0072
Booth3235-0077
Booth3235-0078
Booth3235-0079
Booth3235-0080
Booth3235-0082
Booth3235-0083
Booth3235-0084
Booth3235-0085
Booth3235-0086
Booth3235-0087
Booth3235-0088
Booth3235-0089
Booth5623-0001"""

for line in LINES.splitlines():
    images = [
        'images/{}00.jpg'.format(line),
        'images/{}01.jpg'.format(line),
        'images/{}02.jpg'.format(line),
    ]
    b.images = images
    b.session_counter += 1
    print(b.generate_strip())