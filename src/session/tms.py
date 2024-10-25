import requests
import json

censorLength = 5
userAgent = "Mozilla/5.0 (iPhone14,3; U; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) Version/10.0 Mobile/19A346 Safari/602.1"

class TMSession:
    """TMSession object"""
    
    def __init__(self, student_id, password):
        """Initiate a TMS Session"""
        self.student_id = student_id
        self.password = password
        self.auth()
        self.protectedPass = TMSession.credsCensor(self.password, censorLength)
        self.protectedSess = TMSession.credsCensor(self.phpsessid, censorLength)
        
    
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
    
    def auth(self):
        if not self.credsVerify():
            raise SessionException("Invalid credentials", 5)
        res = requests.post('https://my.beu.edu.az',
            data=f"username={self.student_id}&password={self.password}&LogIn=",
            headers= {
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
                return
        raise SessionException("Couldn't find session ID", 8)
    
    def json(self):
        return json.dumps({"student_id": self.student_id, "password": self.protectedPass, "phpsessid": self.protectedSess})
    

class SessionException(Exception):
    """Session Exception

            status_code:
                6: Set-Cookie header is empty
                7: Bad response code
                8: Couldn't get a PHPSESSID
                9: Empty response
                10: Bad credentials
    """
    def __init__(self, message, error_code):
        self.message = message
        super().__init__(self.message)
    
    def __str__(self):
        return f"{self.message} (Error code: {self.error_code})"