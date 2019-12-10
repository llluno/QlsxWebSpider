from lxml import etree
import os
from functools import reduce
import pandas as pd
import arrow


class AnalyseDaya:
    #要分析的事项列表xls
    __analyseFilename = '1206温州.xls'

    def run(self):
        df = pd.read_excel(self.__analyseFilename, sheet_name='Sheet1')['权力内部编码']
        res = []
        for ic in df:
            if ic != 'cef8e360-d18d-4928-a977-1778e1fb58a5':
                continue
            with open('{}/../../数据/{}'.format(os.getcwd(), ic)) as fp:
                tmp = fp.read()
                tmp = tmp.replace('<br>', '\n')
                # print(tmp)
                et = etree.HTML(tmp)
                # print(ic)
                res.append(self.produce(et, ic))
                # materialProduce(et, ic)

        ddf = pd.DataFrame(res)
        ddf.to_excel('test.xls', index=False)



    def materialProduce(self, et, ic):
        #材料名称
        print(et.xpath('//*[@id="sbcl"]/div[3]/div/div[1]/span[1]/following-sibling::span/p//text()'))

        #其余属性
        print(list(filter(lambda x : x.strip(), et.xpath('//div[@class="sbcl_tables_item"]//text()'))))

    def produce(self, et, ic):

        jbxx = list(filter(lambda x: x not in ['事项信息', '办事信息', '结果信息'], map(lambda x: x.strip(), et.xpath('//div[@class="jbxx_tables"]//td/div/text()'))))
        newJbxx = []
        for i in range(0, len(jbxx) - 1):
            if jbxx[i] != jbxx[i + 1]:
                newJbxx.append(jbxx[i])
        jbxx = newJbxx
        # print(jbxx)

        jbxxDic = {'内部编码': ic}
        for i in range(0, len(jbxx), 2):
            # print('{} {}\n'.format(jbxx[i], jbxx[i+1]))
            if jbxx[i] not in jbxxDic and jbxx[(i + 1) % len(jbxx)] not in jbxxDic:
                jbxxDic[jbxx[i]] = jbxx[(i + 1) % len(jbxx)]


        #法定办结时限和承诺办结期限
        totalCompleteTime = et.xpath('//table[@id="table1"]//div[contains(text(), "法定办结时限")]/../..//span/text()')
        lowComplete = totalCompleteTime[0].strip()
        curComplete = totalCompleteTime[1].strip()
        jbxxDic['法定办结时限'] = lowComplete
        jbxxDic['承诺办结时限'] = curComplete


        # 具体地址
        address = ''.join([k.strip() for k in et.xpath('//span[contains(text(), "具体地址")]/..//span[@class="Cons"]/text()')])
        jbxxDic['具体地址'] = address

        #工作时间
        workTime = ''.join([k.strip() for k in et.xpath('//span[contains(text(), "办理时间")]/..//span[@class="Cons"]/text()')])
        jbxxDic['工作时间'] = workTime

        #联系方式
        phone = ''.join([k.strip() for k in et.xpath('//span[contains(text(), "联系电话")]/..//span[@class="Cons"]/text()')])
        jbxxDic['联系方式'] = phone

        #有表格的 办理环节，如果空就是不是表格形式
        applyLink = list(filter(lambda x: x.strip() , [''.join(x.split()) for x in et.xpath('//div[@class="bllc_con"]//td[1]//text()')]))
        rowspan = et.xpath('//div[@class="bllc_con"]//td[1]/@rowspan')
        print(rowspan)
        jbxxDic['办理环节'] = ''.join(applyLink)
        jbxxDic['办理环节数'] = len(applyLink) - 1
        print(applyLink)

        #是否收费
        needMoney = ''.join(et.xpath('//div[@class="sfsf"]//div[@class="sfyjCon"]//text()')).strip()
        # print(needMoney)
        jbxxDic['是否收费'] = needMoney

        #收费依据
        chargeTicket = ''.join(et.xpath('//div[@class="sfyj"]//div[@class="sfyjCon"]//text()')).strip()
        # print(chargeTicket)
        jbxxDic['收费依据'] = chargeTicket

        #是否支持网上支付
        webCharge = ''.join(et.xpath('//div[@class="sfzccwszf"]//div[@class="sfyjCon"]//text()')).strip()
        jbxxDic['是否支持网上支付'] = webCharge

        #收费项目
        chargeItems = reduce(lambda x, y: x + y, map(lambda x: x.strip(), et.xpath('//div[@class="sfbz_tables"]//span[@class="sfxmmc_cons clearfix"]//text()')), '')
        jbxxDic['收费项目'] = chargeItems
        #常见问题
        faq = reduce(lambda x, y: x + y, map(lambda x: x.strip(), et.xpath('//div[@class="cjwt_table"]//text()')), '')
        # print(faq)
        jbxxDic['常见问题'] = faq

        #咨询电话
        askPhone = ''.join(et.xpath('//div[@class="zxfs"]//p[@class="zxdh clearfix"]/span[@class="zxfsCon"]//text()')).strip()
        jbxxDic['咨询电话'] = askPhone

        # print(askPhone)

        #咨询地址
        askAddress = ''.join(et.xpath('//div[@class="zxfs"]//p[@class="zxdz clearfix"]/span[@class="zxfsCon"]//text()')).strip()
        jbxxDic['咨询地址'] = askAddress

        #投诉电话
        complainPhone = ''.join(et.xpath('//div[@class="jdtsfs"]//p[@class="zxdh clearfix"]/span[@class="jdtsfsCon"]//text()')).strip()
        # print(complainPhone)
        jbxxDic['投诉电话'] = complainPhone

        #投诉地址
        complainAddress = ''.join(et.xpath('//div[@class="jdtsfs"]//p[@class="zxdz clearfix"]/span[@class="jdtsfsCon"]//text()')).strip()
        # print(complainAddress)
        jbxxDic['投诉地址'] = complainAddress

        # print(jbxxDic)
        self.__getMaterials('test', et)

        return jbxxDic


    def analyse(self):
        df = pd.read_excel('test.xls', sheet_name='Sheet1')
        totRes = []
        for index, row in df.iterrows():
            error = ''
            idx = 1
            # 承诺办结时间为即办，办件类型必须为即办件，事项审查类型为即审即办
            if row['承诺办结时限'] == '即办':
                if row['办件类型'] != '即办件' or row['事项审查类型'] != '即审即办':
                    error += '{}. 承诺办结时间为即办，办件类型必须为即办件，事项审查类型为即审即办\n'.format(idx)
                    idx += 1
            # 承诺办结时间非即办，办件类型必须为承诺件，事项审查类型为先审后批
            if row['承诺办结时限'] != '即办':
                if row['办件类型'] != '承诺件' or row['事项审查类型'] != '前审后批':
                    error += '{}. 承诺办结时间非即办，办件类型必须为承诺件，事项审查类型为先审后批\n'.format(idx)
                    idx += 1
            # 如审批结果名称为XX证则审批结果类型为出证办结
            if row['审批结果名称'].endswith('证'):
                if row['审批结果类型'] != '出证办结':
                    error += '{}. 如审批结果名称为XX证则审批结果类型为出证办结\n'.format(idx)
                    idx += 1
            # 4.如审批结果名称为XX文则审批结果类型为出文办结
            if row['审批结果名称'].endswith('文'):
                if row['审批结果类型'] != '出文办结':
                    error += '{}. 如审批结果名称为XX文则审批结果类型为出文办结\n'.format(idx)
                    idx += 1
            #如审批结果名称为XX批复则审批结果类型为审批办结
            if row['审批结果名称'].endswith('批复'):
                if row['审批结果类型'] != '审批办结':
                    error += '{}. 如审批结果名称为XX批复则审批结果类型为审批办结\n'.format(idx)
                    idx += 1
            # 到办事现场次数非0次事项需填写原因说明
            if row['到办事现场次数'] != '0次':
                if pd.isnull(row['必须现场办理原因说明']):
                    error += '{}. 到办事现场次数非0次事项需填写原因说明\n'.format(idx)
                    idx += 1
            # 跑0次事项除非有特殊原因外不必填写原因说明
            if row['到办事现场次数'] == '0次':
                if row['必须现场办理原因说明'] != '无':
                    error += '{}. 跑0次事项除非有特殊原因外不必填写原因说明\n'.format(idx)
                    idx += 1

            #到现场办事次数为0次事项并且不支持网办事项，办理形式需支持快递收件
            if row['到办事现场次数'] == '0次':
                if row['是否网办'] != '是' and '邮寄申请' not in row['办理形式']:
                    error += '{}. 到现场办事次数为0次事项并且不支持网办事项，办理形式需支持快递收件\n'.format(idx)
                    idx += 1

            # 网办深度四级到现场办事次数应为0次
            if row['网上办理深度'] == '全程网办（Ⅳ级）':
                if row['到办事现场次数'] != '0次':
                    error += '{}. 网办深度四级到现场办事次数应为0次\n'.format(idx)
                    idx += 1

            # 是否收费为是，则需填写收费依据、是否支持网上支付、收费项目名称、收费标准
            if row['是否收费'] == '是':
                if pd.isnull(row['收费依据']) or pd.isnull(row['是否支持网上支付']) or pd.isnull(row['收费项目']):
                    error += '{}. 是否收费为是，则需填写收费依据、是否支持网上支付、收费项目名称、收费标准\n'.format(idx)
                    idx += 1

            #咨询电话和投诉电话不同且必须有，带区号0577
            if pd.isnull(row['咨询电话']) or pd.isnull(row['投诉电话']) or row['咨询电话'] == row['投诉电话'] or ('0577' not in row['咨询电话'] or '0577' not in row['投诉电话']):
                error += '{}. 咨询电话和投诉电话不同且必须有，带区号0577\n'.format(idx)
                idx += 1

            # 咨询和投诉地址不为空且不相等
            # if pd.isnull(row['咨询地址']) or pd.isnull(row['投诉地址']) or row['咨询地址'] == row['投诉地址']:
            #     error += '{}. 咨询和投诉地址不为空且不相等\n'.format(idx)
            #     idx += 1

            #服务对象需与主题分类一致。例如法人事项主题分类为法人，必须有法人主题，且自然人主题应为空。
            res = 0
            if '法人' in row['服务对象']:
                res ^= 1
            if '个人' in row['服务对象']:
                res ^= 1
            if row['自然人主题分类'] != '无':
                res ^= 1
            if row['法人主题分类'] != '无':
                res ^= 1
            if res != 0:
                error += '{}. 服务对象需与主题分类一致。例如法人事项主题分类为法人，必须有法人主题，且自然人主题应为空。\n'.format(idx)
                idx += 1

            #许可类事项一定要有一个常见问题
            if row['事项类型'] == '行政许可' and '暂无常见问题' in row['常见问题']:
                error += '{}. 许可类事项一定要有一个常见问题\n'.format(idx)
                idx += 1

            # 联系方式不为空且和投诉电话不相等，并且带0577
            if pd.isnull(row['联系方式']) or row['联系方式'] == row['投诉电话'] or '0577' not in row['联系方式']:
                error += '{}. 联系方式不为空且和投诉电话不相等，并且带0577\n'.format(idx)
                idx += 1

            # 许可类事项环节可能存在异常（必须为表格且包含受理、审核、审批、办结、送达等环节）
            if row['办理环节数'] < 5 and row['事项类型'] == '行政许可':
                error += '{}. 许可类事项环节可能存在异常（必须为表格且包含受理、审核、审批、办结、送达等环节）\n'.format(idx)
                idx += 1

            # 如果有审批结果就要有样本
            if row['审批结果名称'] != '无':
                if row['审批结果样本'] == '无样本':
                    error += '{}. 如果有审批结果就要有样本\n'.format(idx)
                    idx += 1
            #如果不收费，不能支持网上支付
            if row['是否收费'] == '不收费':
                if row['是否支持网上支付'] == '支持':
                    error += '{}. 如果不收费，不能支持网上支付\n'.format(idx)
                    idx += 1

            totRes.append(error)

        df['错误情况'] = pd.Series(totRes)
        oldDf = pd.read_excel(self.__analyseFilename, sheet_name='Sheet1', usecols=['权力内部编码', '部门名称', '权力基本码'])
        df:pd.DataFrame = pd.merge(df, oldDf, left_on='内部编码', right_on='权力内部编码').drop(columns='内部编码')
        dep = df.pop('部门名称')
        df.insert(0, '部门名称', dep)
        df.to_excel('{}温州错误情况.xls'.format(arrow.now().format('MMDD')), index=False)



    def __getMaterials(self, response, et):
        # 判断是否分类材料，能的话需要重新请求
        # et = etree.HTML(response)
        isMaterialSplit = et.xpath('//*[@id="sbcl"]//div[@class="apply_material"]')
        if isMaterialSplit:
            # 拿到impleCode
            impleCode = et.xpath('//*[@id="impleCode"]')
            totalMaterialValues = et.xpath('//div[@class="apply_material"]//li//@value')
            return ';'.join(totalMaterialValues)

a = AnalyseDaya()
a.run()
# a.analyse()