import requests
import json

HOST = 'my.beu.edu.az'
ROOT = 'https://' + HOST + '/'
censorLength = 5
userAgent = "Mozilla/5.0 (iPhone14,3; U; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) Version/10.0 Mobile/19A346 Safari/602.1"

class TMSession:
    """TMSession object"""
    
    def __init__(self, student_id, password):
        """Initiate a TMS Session"""
        self.student_id = student_id
        self.password = password
        self.protectedPass = TMSession.credsCensor(self.password, censorLength)
    
    def __str__(self):
        return f"[{self.student_id}:{self.protectedPass}] -> {self.protectedSess}"
    
    def credsCensor(secret, censorLength):
        secretLength = len(secret)
        if secretLength >= censorLength * 2:
            secret = secret[0: censorLength] + "*" * (secretLength - censorLength)
        else:
            secret = "*" * secretLength
        return secret
        
    def credsVerify(self):
        """Verify username/password

        Returns:
            bool: Returns true if verification passed
        """
        if (not len(str(self.student_id)) == 9):
            return False
        return True
    
    def get(self, target):
        res = requests.post(ROOT + target,
            headers = {
                "Host": HOST,
                "Cookie": "PHPSESSID=" + self.phpsessid,
                "User-Agent": userAgent
            },
            allow_redirects=False)
        if not res.status_code == 200:
            raise SessionException("GET Failed", 11)
        return res.text
        
    
    def auth(self):
        if not self.credsVerify():
            raise SessionException("Invalid credentials", 5)
        res = requests.post(ROOT + 'auth.php',
            data = f"username={self.student_id}&password={self.password}&LogIn=",
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": userAgent
            },
            allow_redirects=False)
        if not res.status_code == 302:
            raise SessionException("Bad credentials", 10)
        cookies = res.headers.get('Set-Cookie')
        if cookies == None:
            raise SessionException("Couldn't get the cookies", 6)
        for header in cookies.replace(' ', '').split(';'):
            if (not header.find('PHPSESSID') == -1):
                self.phpsessid = header.split('=')[1]
                self.protectedSess = TMSession.credsCensor(self.phpsessid, censorLength)
                return
        raise SessionException("Couldn't find session ID", 8)
    
    def logout(self):
        res = requests.get(ROOT + 'logout.php',
            headers = {
                "Host": HOST,
                "Cookie": "PHPSESSID=" + self.phpsessid + "; uname=" + self.student_id,
                "User-Agent": userAgent
            },
            allow_redirects=False)
        if not res.status_coed == 302:
            raise SessionException("Couldn't logout", 11)
        
    
    def toJSON(self):
        return json.dumps({
            "student_id": self.student_id,
            "password": self.protectedPass,
            "sessionID": self.protectedSess
        })

class SessionException(Exception):
    """Session Exception

        Returns:
            status_code:
                6: Set-Cookie header is empty
                7: Bad response code
                8: Couldn't get a PHPSESSID
                9: Empty response
                10: Bad credentials
                11: Couldn't logout
    """
    def __init__(self, message, error_code):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)
    
    def __str__(self):
        return f"{self.message} (Error code: {self.error_code})"