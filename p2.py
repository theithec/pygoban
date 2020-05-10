import re
sgf=""";W[oo]WL[30]OW[5]
;B[]BL[452.252]
;W[]WL[30]OW[5]TW[aa][ba][ca][da][ea][fa][ka][la][ma][na][oa][qa][ra][sa][ab][bb][db][eb][gb][ib][jb][kb][lb][mb][ob][qb][ac][ec][fc][gc][ic][kc][lc][rc][sc][ad][dd][ed][fd][gd][id][jd][kd][be][de][ie][je][ke][le][se][af][hf][ag][bg][ih][hi][an][bn][cn][dn][en][nn][bo][co][do][eo][no][po][ap][bq][pq][qq][pr][qr][rr][sr][ps][qs][rs][ss]TB[nf][of][eg][mg][ng][og][eh][lh][oh][ph][qh][rh][li][ni][pi][qi][si][bj][lj][mj][rj][sj][jk][kk][rk][sk][rl][sl][rm][sm][sn][ip][fq][gq][hq][jq][kq][hr][ir][jr][lr][fs][gs][hs][is][js][ks][ls]C[ruxy [7k\]: ty
lotek [6k\]: Thx
]"""


lines = [clean for part in sgf.split(";") if (clean:=part.strip())]
print(lines)
#lines = ["A[bb]\n"]

for part in lines:
    print()
    while True:
        print("p", part)
        m = re.match(
            #r"([A-Z]{1,2})\[(.*?)\](?<!\\)([A-Z].*)",
            #r"([A-Z]{1,2})\[(.*?)\](?<!\\)([A-Z$].*)",
            #r"([A-Z]{1,2})(\[.*?\](?<!\\))[A-Z]|\Z",
            #r"([A-Z]{1,2})(\[.*?\](?<!\\))$|\Z|[A-Z]",
            #r"([A-Z]{1,2})(\[.*?(?<!\\)\]).*",
            r"([A-Z]{1,2})((?:\[.*?(?<!\\)\])+).*",
            part,
            flags=re.DOTALL)
        if m:

            print(m)
            key, val = m.groups()
            print("k", key)
            print("v", val)
            #print("r", rest)
            print("SP", m.span(2))
            part = part[m.span(2)[1]:]
            print()
        else:
            if part.strip():
                print("NO MATCH FOR", part)
            break
