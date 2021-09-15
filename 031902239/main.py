import pypinyin
import sys

Dictionary = {}   #字典
Total = 0       #敏感词总数
answer = []     #输出内容
SignSet = [' ','_','，','、','。','·','.','…','`',',','"','“',':','：',';',
           '?','？','！','!','<','>','=','~','+','-','*','%','/','^','|',
           '\\','\'','&','#','@','$','￥','(',')','[',']','{','}','【','】',
           '《','》','0','1','2','3','4','5','6','7','8','9']      #符号集合

class DFA(object):

    #初始化
    def __init__(self):
        super(DFA,self).__init__()
        self.senwords_tree = {}  #敏感词树
        self.delimit = '\x00'

    #排列组合[完整拼音，拼音首字母]的嵌套列表
    def Combine(self,table,senword,word_len,count,charString):   #word_len:敏感词长度
        if count == word_len:                  #当长度到达该敏感词长度为递归出口
            Dictionary[charString] = senword   #以charString为索引字符串，将其与正确的敏感词匹配放入字典
            self.AddSensitiveWords(charString)  #将索引加到敏感词树上
            return
        self.Combine(table,senword,word_len,count+1,charString+table[count][0])
        self.Combine(table,senword,word_len,count+1,charString+table[count][1])
        return

    #读取敏感词
    def ReadSensitiveWords(self,words_path):
        words_file = open(words_path,encoding='utf-8')
        while 1:
            table = []   #单个字全拼和首字母的嵌套列表
            senword = words_file.readline()   #按行读入敏感词
            senword = senword.rstrip('\n')    #去掉换行符
            # 对敏感词循环获取每个字,即i为一个字
            for i in senword:
                whole_pin = ""
                first_pin = ""
                #以下循环是对单个字循环
                for j,pin in enumerate(pypinyin.pinyin(i,style = pypinyin.NORMAL)):  #NORMAL是去掉拼音声调
                    whole_pin += "".join(pin)
                    first_pin += "".join(pin[0][0])
                    # table为每个字[完整拼音,拼音首字母]列表
                    table.append([whole_pin,first_pin])
            # 对table进行排列组合
            self.Combine(table,senword,len(senword),0,'')
            if not senword:
                break

    #添加敏感词
    def AddSensitiveWords(self,charString):
        if not charString:
            return
        sen_tree = self.senwords_tree
        for i in range(len(charString)):
            if charString[i] in sen_tree:
                # 在树中则继续向下跟踪
                sen_tree = sen_tree[charString[i]]
            else:
                for j in range(i,len(charString)):
                    # 不在树种则建立一个新结点
                    sen_tree[charString[j]] = {}
                    # 新建节点作为最后一个节点
                    last_node = sen_tree
                    last_char = charString[j]
                    sen_tree = sen_tree[charString[j]]
                    # 在末尾加上结束符（self.delimit为索引，值为0）
                last_node[last_char] = {self.delimit:0}
                break
            if i == len(charString)-1:
                sen_tree[self.delimit] = 0

    #过滤敏感词
    def FilterSensitiveWords(self,linecount,singleLine ):
        sen_count = 0
        begin = 0
        # 从begin的位置开始检测该行
        while begin < len(singleLine):
            # s1用于存放寻找敏感词的索引
            s1 = ""
            counter = 0
            sign1, sign2 = 0, 0
            # 切片获取begin开始的内容
            content = singleLine[begin:]
            sen_tree = self.senwords_tree
            # 对于从begin开始到本行末尾进行循环,i是一个字
            for i in content:
                # s存单个字的拼音
                s = ''
                for j,pin in enumerate(pypinyin.pinyin(i,style=pypinyin.NORMAL)):
                    s += ''.join(pin)
                    s = s.lower()
                # 若已找到了敏感词的头且s[0]内容为特殊符号，则计步器+1，跳过该字符
                p1 = begin
                if s[0] in SignSet and sign1 == 1 :
                    counter += 1
                    continue
                for j in s:
                    # 能在树上找到
                    if j in sen_tree:
                        # 将标志sign1置为1（用于后续处理遇到敏感词中间出现符号的情况）
                        s1 += "".join(j)
                        sign1 = 1
                        # 此敏感词搜寻到尾了
                        if self.delimit in sen_tree[j]:
                            # 此敏感词搜索完毕，标志复位
                            sign1 = 0
                            # begin累加上计步器，开始寻找下一个敏感词
                            begin += counter
                            # 将begin的新位置赋值给p2，p1到p2即原文中敏感词的内容
                            p2 = begin
                            # 敏感词计数+1
                            sen_count += 1
                            # 以s1为索引在字典中搜索出敏感词的正确写法
                            correct = Dictionary[s1]
                            # 将该敏感词对应的输出存到列表answer中
                            answer.append("Line" + str(linecount) + ":<" + correct + ">" + singleLine[p1:p2+1])
                            sign2 = 1
                        # 该敏感词搜索还未到尾,则向下跟踪
                        else:
                            sen_tree = sen_tree[j]
                    # 不能在树上找到
                    else:
                        sign2 = 1
                        break
                if sign2 == 1:
                    break
                counter += 1
            begin += 1
        return sen_count

if __name__ == "__main__":
    # f为DFA的实例化对象
    f = DFA()
    #读取敏感词文件
    f.ReadSensitiveWords(sys.argv[1])
    #打开文本
    orgfile = open(sys.argv[2],encoding='utf-8')
    sign = 0    #标志空行数
    linecount = 1    #行号
    while 1:
        #按行读取文件内容并去掉换行符
        singleLine = orgfile.readline()
        singleLine = singleLine.rstrip('\n')
        #过滤单行敏感词，返回该行敏感词数
        sen_count = f.FilterSensitiveWords(linecount,singleLine)
        linecount +=1
        Total += sen_count   #累加敏感词数
        #若为空行，标志自增1
        if not singleLine:
            sign += 1
        #若出现非空行，则将标志复位
        else:
            sign = 0
        #当空行数大于3时，判定为文本识别完毕，此时退出
        if sign > 3:
            break
    #关闭文本文件
    orgfile.close()
    #将敏感词总数存入answer列表
    answer.append(str(Total))
    #规定写文件的路径
    #path = "D:\\pythonProject2\\"+"ans.txt"
    path = sys.argv[3]
    ansfile = open(path,'w')
    ansfile.write("total:")
    ansfile.write(str(answer[len(answer)-1]))
    ansfile.write('\n')
    for i in range(len(answer)-1):
        ansfile.write(str(answer[i]))
        ansfile.write('\n')
