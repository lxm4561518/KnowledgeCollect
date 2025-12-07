import json
import os

cookie_str = "buvid3=140F8535-E6E7-A862-BE7D-1E5796848FB513606infoc; b_nut=1764722413; _uuid=83D3AB53-D7EC-251B-8726-6255B6FFD6DD15733infoc; home_feed_column=5; buvid4=E101E224-EED5-D330-A2EA-9AC77CD47CFD16207-025120308-vb2QuZ5kkYMwhm3z3H8d0w%3D%3D; CURRENT_QUALITY=0; rpdid=|(k|kYuYR)~|0J'u~YR~kkRJY; DedeUserID=1200205249; DedeUserID__ckMd5=51b830404fd956b0; theme-tip-show=SHOWED; theme-avatar-tip-show=SHOWED; SESSDATA=81483fab%2C1780538055%2Ccdeaf%2Ac1CjDzlt8reyKd5f6voKJ9cCmN7S_Ip5UppovSr-qIqu6sDT8tEBlCryNO4oTN1Ah-HBsSVmEyRE1LSDVXU1MwZ0NTenlDejZTV00tRmNRZzI4aUV6bU4wdnlGMWg2T0RraUNxem1rajZISE9uZndsZzFtc3U3ZXZXY0VYN0VmdUpxXy1tOGVHcDh3IIEC; bili_jct=3040c14810579e6f6dee11e7a22627ee; sid=4yb34nb9; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjUyNzI0MDIsImlhdCI6MTc2NTAxMzE0MiwicGx0IjotMX0.bK3F6V7-6wpuPED1MMV0OQ4JQap3Seh3BXlosZJDztI; bili_ticket_expires=1765272342; fingerprint=b97bd742199c93cd676f4ed86e432ab4; buvid_fp_plain=undefined; buvid_fp=b97bd742199c93cd676f4ed86e432ab4; browser_resolution=1920-911; b_lsid=6A95B5D2_19AF7F4CD6C; bp_t_offset_1200205249=1143580599278108672; CURRENT_FNVAL=4048"

cookies = []
for item in cookie_str.split(";"):
    item = item.strip()
    if not item:
        continue
    if "=" in item:
        name, value = item.split("=", 1)
        cookies.append({
            "name": name,
            "value": value,
            "domain": ".bilibili.com",
            "path": "/"
        })

output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "cookies"))
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

output_path = os.path.join(output_dir, "bilibili.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(cookies, f, indent=2)

print(f"Saved {len(cookies)} cookies to {output_path}")
