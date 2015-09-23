#'!/usr/bin/python

# SAVE TO:  /Library/Frameworks/Python.framework/Versions/2.5/lib/python2.5
# or another folder in sys.path

# 02 and 12:    Kodak 16mm/35mm
# 13:           Fuji 16mm
# 03:           Fuji 35mm
orientation = { '0': 'Left to right, top to bottom',
               '1': 'Right to left, top to bottom',
               '2': 'Left to right, bottom to top',
               '3': 'Right to left, bottom to top',
               '4': 'Top to bottom, left to right',
               '5': 'Top to bottom, right to left',
               '6': 'Bottom to top, left to right',
               '7': 'Bottom to top, right to left'}

descriptor = {'0':'User-defined',
'1':'Red',
'2':'Green',
'3':'Blue',
'4':'Alpha',
'6':'Luminance',
'7':'Chrominance',
'8':'Depth',
'9':'Composite video',
'50':'RGB',
'51':'RGBA',
'52':'ABGR',
'100':'CbYCrY',
'101':'CbYaCrYa',
'102':'CbYCrY',
'103':'CbYCra',
'150':'User-defined 2-component element',
'151':'User-defined 3-component element',
'152':'User-defined 4-component element',
'153':'User-defined 5-component element',
'154':'User-defined 6-component element',
'155':'User-defined 7-component element',
'156':'User-defined 8-component element',
}


transfer = {
"0":"User-defined",
"1":"Printing density",
"2":"Linear",
"3":"Logarithmic",
"4":"Unspecified video",
"5":"SMPTE 240M",
"6":"CCIR 709-1",
"7":"CCIR 601-2 system B or G",
"8":"CCIR 601-2 system M",
"9":"NTSC composite video",
"10":"PAL composite video",
"11":"Z linear",
"12":"Z homogeneous", 
}

video_signal = {
"0":"Undefined",
"1":"NTSC",
"2":"PAL",
"3":"PAL-M",
"4":"SECAM",
"50":"YCBCR CCIR 601-2 525-line, 2:1 interlace, 4:3 aspect ratio",
"51":"YCBCR CCIR 601-2 625-line, 2:1 interlace, 4:3 aspect ratio",
"100":"YCBCR CCIR 601-2 525-line, 2:1 interlace, 16:9 aspect ratio",
"101":"YCBCR CCIR 601-2 625-line, 2:1 interlace, 16:9 aspect ratio",
"150":"YCBCR 1050-line, 2:1 interlace, 16:9 aspect ratio",
"151":"YCBCR 1125-line, 2:1 interlace, 16:9 aspect ratio",
"152":"YCBCR 1250-line, 2:1 interlace, 16:9 aspect ratio",
"200":"YCBCR 525-line, 1:1 progressive, 16:9 aspect ratio",
"201":"YCBCR 625-line, 1:1 progressive, 16:9 aspect ratio",
"202":"YCBCR 787.5-line, 1:1 progressive, 16:9 aspect ratio",
}



colorimetric = {
"0":"User-defined",
"1":"Printing density",
"4":"Unspecified video",
"5":"SMPTE 240M",
"6":"CCIR 709-1",
"7":"CCIR 601-2 system B or G",
"8":"CCIR 601-2 system M",
"9":"NTSC composite video",
"10":"PAL composite video",                     
}



film_mfg_id = {'02':'Kodak', '12':'Kodak',
               '03':'Fuji', '13':'Fuji'}

edgecode = {'02': {
				'00': ['KP', '5600'],
				'01': ['EK', '5201 Vision2 50D' ],
				'05': ['EQ', '5205 Vision2 250D'],
				'12': ['EM', '5212 Vision2 100T'],
				'14': ['KX', 'SO-214 SFX 200T'],
				'17': ['EL', '5217 Vision2 200T'],
				'18': ['EH', '5218 Vision2 500T'],
				'19': ['EJ', '5219 Vision3 500T'],
				'20': ['KY', '5620 Prime Time'],
				'22': ['KE', '5222'],
				'24': ['KL', '5224'],
				'29': ['EB', '5229 Vision2 Expression 500T'],
				'31': ['KH', '5231'],
				'34': ['KD', '5234'],
				'42': ['EV', '5242 Vision Intermediate'],
				'43': ['KA', '5243'],
				'44': ['KV', '5244'],
				'45': ['KK', '5245 Vision 50D'],
				'46': ['KI', '5246 Vision 250D'],
				'47': ['KB', '5247'],
				'48': ['KM', '5248'],
				'49': ['KO', '5249'],
				'63': ['EE', '5263 Vision 500T'],
				'52': ['KS', '5252'],
				'74': ['KZ', '5274 Vision 200T'],
				'77': ['KQ', '5277'],
				'79': ['KU', '5279'],
				'84': ['EG', '5284 Vision Expression 500T'],
				'85': ['EA', '5285 100D'],
				'87': ['KW', '5287'],
				'89': ['KR', '5289 Vision 800T'],
				'93': ['KL', '5293'],
				'94': ['KG', '5294'],
				'95': ['KF', '5295'],
				'96': ['KF', '5296'],
				'97': ['KC', '5297'],
				'98': ['KT', '5298']				},
			'03': {
				'43': ['FN43', 'ETERNA Vivid 160T (35mm)' ],
				'53': ['FN53', 'ETERNA 250T (35mm)'],
				'83': ['FN83', 'ETERNA 400T (35mm)'],
				'73': ['FN73', 'ETERNA 500T (35mm)'],
				'22': ['FN22', 'Fuji F-64D (35mm)'],
				'63': ['FN63', 'ETERNA 250D (35mm)'],
				'92': ['FN92', 'REALA 500D (35mm)']    },            
				
				
			'12': {
				'01': ['EK', '7201 Vision2 50D' ],
				'05': ['EQ', '7205 Vision2 250D'],
				'12': ['EM', '7212 Vision2 100T'],
				'17': ['EL', '7217 Vision2 200T'],
				'18': ['EH', '7218 Vision2 500T'],
				'19': ['EJ', '7219 Vision3 500T'],
				'22': ['KE', '7222'],
				'29': ['EB', '7229 Vision2 Expression 500T'],
				'31': ['KH', '7231'],
				'34': ['KD', '7234'],
				'42': ['EV', '7242 Vision Intermediate'],
				'43': ['KA', '7243'],
				'44': ['KV', '7244'],
				'45': ['KK', '7245 Vision 50D'],
				'46': ['KI', '7246 Vision 250D'],
				'47': ['KB', '7247'],
				'48': ['KM', '7248'],
				'63': ['EE', '7263 Vision 500T'],
				'65': ['EC', '7265'],
				'66': ['ED', '7266'],
				'72': ['KS', '7272'],
				'74': ['KZ', '7274 Vision 200T'],
				'77': ['KQ', '7277'],
				'79': ['KU', '7279'],
				'84': ['EG', '7284 Vision Expression 500T'],
				'87': ['KW', '7287'],
				'92': ['KN', '7292'],
				'93': ['KL', '7293'],
				'94': ['KG', '7294'],
				'96': ['KF', '7296'],
				'97': ['KC', '7297'],
				'98': ['KT', '7298'],
				'99': ['EI', '7299']				},

			    
			'13': {
				'43': ['FN43', 'ETERNA Vivid 160T' ],
				'53': ['FN53', 'ETERNA 250T'],
				'83': ['FN83', 'ETERNA 400T'],
				'73': ['FN73', 'ETERNA 500T'],
				'22': ['FN22', 'Fuji F-64D'],
				'63': ['FN63', 'ETERNA 250D'],
				'92': ['FN92', 'REALA 500D']            }
				}

