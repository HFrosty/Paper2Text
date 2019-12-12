import sys
import os
import re
import shutil
import tempfile

class PaperEnt:
    def __init__(self,filename="",title="",abstract="",auteurs="",biblio=""):
        self.filename=filename
        self.title=title
        self.abstract=abstract
        self.auteurs=auteurs
        self.biblio=biblio

    def toText(self):
        return self.filename+'\n'+self.title+'\n'+self.auteurs+self.abstract+'\n'+self.biblio

    def toXML(self):
        return """<article>\n
            <preamble>"""+self.filename+"""</preamble>\n
            <title>"""+self.title+"""</title>\n
            <auteur>"""+self.auteurs+"""</auteur>\n
            <abstract>"""+self.abstract+"""</abstract>\n
            <biblio>"""+self.biblio+"""</biblio>\n
            </article>"""

class PersiFichierTexte:
    @staticmethod
    def persiToString(persi):
        with open(persi,'r') as textFile:
            return textFile.read().rstrip()

    @staticmethod
    def stringToPersi(string,filePath):
        with open(filePath,"w") as textFile:
            print(string,file=textFile)

class Parser:
    def __init__(self,content):
        self.content=content
        dictionnaryPath = os.path.dirname(os.path.realpath(__file__))+os.path.sep+"firstnames.txt"
        # firstnames est une liste de str
        with open(dictionnaryPath, "r") as dictionnaryFile:
            self.firstnames = dictionnaryFile.readlines()

    # retourne le numero de la premiere ligne contenant un prenom
    # on suppose que le fichier firstnames.txt se trouve dans le meme repertoire
    def nbFirstLineWithName(self):
        # parcourir le contenu a parser
        fileLines = self.content.split("\n")
        for line in fileLines:
            for firstname in self.firstnames:
                for word in re.findall(r"[\w']+", line):
                    if word == (firstname.upper()[0] + firstname.lower()[1:-1]):
                        return self.content.find(line)
        

    # premiere ligne ou contenu avant la premiere ligne contenant un prenom
    def getTitle(self):
        return self.content[0:self.nbFirstLineWithName()]

    # contenu entre abstract et introduction
    def getAbstract(self):
        ss = re.search('(?is)abstract(.*?)introduction',self.content)
        if ss:
            return ss.group(1).replace('\n',' ')
        return ""

    # entre le titre et l'abstract
    def getAuteurs(self):
        title = self.getTitle()
        print("Title: " + title)
        ss = re.search('(?is)'+title+'(.*?)abstract',self.content)
        if ss:
            return ss.group(1).replace('\n',' ')
        return ""
    # derniere page ou après Aknowledgments et References
    def getBiblio(self):
        ss = re.search('(?is)\nreferences\n(.*?)\Z',self.content)
        if ss:
            return ss.group(1).replace('\n',' ')
        return ""

class Manager:
    def __init__(self):
        # on suppose que le targetDir est dans le meme repertoire que le script
        self.targetDir=os.path.dirname(os.path.realpath(__file__))+os.path.sep+sys.argv[1]
        self.outputDir=self.targetDir+os.path.sep+"output"
        self.tmpDir="./tmp"
        self.removeTemporaryFolder()
        os.mkdir(self.tmpDir, 0o755)
        self.analyseTargetFolder()
        index = 0
        self.choices = []
        for file in self.files:
            self.choices.insert(index, 0)

    def createTemporaryFiles(self):
        # convertir les PDF en format txt avec pdftotext dans un dossier tmp
            index = 0
            for filename in self.files:
                if self.choices[index] == 1 and filename.endswith('.pdf'):
                    f = filename.replace(" ","\ ")
                    os.system("pdftotext "+self.targetDir+os.path.sep+f+" "+self.tmpDir+os.path.sep+f[:-3]+"txt")
                index += 1

    def convert(self):
        # # deposer les sorties au format .txt, avec meme nom que pdf respectif
        for filename in os.listdir(self.tmpDir):
            # parsing vers entite Paper
            paper = PaperEnt()
            parser = Parser(PersiFichierTexte.persiToString(self.tmpDir+os.path.sep+filename))
            paper.filename=filename[:-4]+".pdf"
            paper.title=parser.getTitle()
            paper.auteurs=parser.getAuteurs()
            paper.abstract=parser.getAbstract()
            paper.biblio=parser.getBiblio()
            # ecriture de l'entite Paper au format texte dans le dossier output
            if len(sys.argv) <= 2 or sys.argv[2] == "-t" :
                PersiFichierTexte.stringToPersi(paper.toText(),self.outputDir+os.path.sep+filename)
            elif sys.argv[2] == "-x" :
                PersiFichierTexte.stringToPersi(paper.toXML(),self.outputDir+os.path.sep+filename[:-3]+"xml")
            else :
                print("Unvalid option " + sys.argv[2])
                break

    def removeTemporaryFolder(self):
        if os.path.exists(self.tmpDir):
                shutil.rmtree(self.tmpDir)

    def displayListOfFiles(self):
        print("Liste des fichiers pris en charges :")
        index = 0
        for file in self.files:
            chosen = " "
            if(self.choices[index] == 1):
                chosen = "X"
            print(str(index) + ". " + chosen + " " + file)
            index += 1

    def askChoiceInput(self):
        self.displayListOfFiles()
        print("---------------------")
        choice = input("Veuillez choisir un fichier à convertir par son numéro (entrez 'c' pour lancer la conversion, 'T' pour une jolie bannière): ")
        if choice.isdigit():
            if int(choice)+1 > len(self.files):
                print("ERREUR: Aucun fichier n'est identifié par l'entrée donnée")
            else:
                if (self.choices[int(choice)] == 1):
                    self.choices[int(choice)] = 0
                else:
                    self.choices[int(choice)] = 1
        else:
            if(choice == "c"):
                return 1
            elif(choice == "T"):
                self.displayBanner()
            else:
                print("ERREUR: Commande inconnue")
        return 0

    def choiceLoop(self):
        loopOver = 0
        while loopOver != 1:
            loopOver = self.askChoiceInput()
    
    def analyseTargetFolder(self):
        index = 0
        self.files = []
        for filename in os.listdir(self.targetDir):
            if filename.endswith(".pdf"):
                self.files.insert(index, filename)
                index += 1

    def displayBanner(self):
        print("")
        print(PersiFichierTexte.persiToString("art"))
        print("")


def main():
    manager = Manager()
    manager.displayBanner()
    manager.choiceLoop()
    manager.createTemporaryFiles()
    manager.convert()
    manager.removeTemporaryFolder()

main()
