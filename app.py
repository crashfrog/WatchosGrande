from flask import Flask, request
from collections import OrderedDict, defaultdict
from jinja2 import Template
from grip import render_page
from datetime import datetime, timedelta

tag = 'untagged'

try:
	tag = str(subprocess.check_output('git describe', shell=True).decode('UTF-8')).rstrip()
except Exception:
	pass

template = Template("""
<!DOCTYPE HTML>
<HTML>
<HEAD>
<TITLE>Watchos</TITLE>
<meta http-equiv="refresh" content="5">
<STYLE>
#page-header,
#page-footer {
    position: fixed;
    width: 100%;
    left: 0;
    background: #ccc;
}

#page-header {
    top: 0;
    height: 100px;
}

#page-footer {
    bottom: 0;
    height: 75px;
}

#page-content {
    padding: 100px 0 75px;
}

#light {
	text-align: left;
}

#spinner {
	text-align: right;
	margin-left: auto;
}

.plus {
	color:slategray;
}

.plus:hover {
	color:black;
}

#dog {
	margin: 7px;
	background-color: whitesmoke;
}

#dog_title {
	display: flex;
}

#dog_tag {
	text-align: center;
	margin-left: auto;
	margin-right: auto;
}

.dog_info {
	font-size:90%;
	color:SlateGrey;
	text-align:center;
	margin:10px;
	display:none;
}

.dogs {
	width: 550px;
	margin-left: auto;
	margin-right: auto;
	font-family:"Courier New", Courier, monospace;
}

.bad_dog {
	color: red;
}

.new_dog {
	color: orange;
}

.good_dog {
	color: green;
}

.inner {
    width: 550px;
    margin-left: auto;
    margin-right: auto;
    text-align: center;
}

</STYLE>
</HEAD>
<BODY>
<div id="wrapper">
    <header id="page-header">
        <div class="inner">
            <h2>Watchos Grande: The Cheesy Process Watchdog</h2><h4>build {{ tag }}</h4>
        </div>
    </header>
    <div id="page-content">
        <div class="dogs">
           {% for dogname, dog in dogs.items() %}
           <div id="dog">
           <div id="dog_title">
           <div id="light">( 
           	<span class="{% if dog.is_new %}
    		new_dog
    		{% elif dog.is_expired %}
    		bad_dog
    		{% else %}
    		good_dog
    		{% endif %}">@</span>
           )</div> 
           <div id="dog_tag"> {{ dogname }} ({{ dog.mean }} avg interval)</div> 
           <div id="spinner_{{ dogname }}" onclick="toggle_visibility('{{ dogname }}')">
           [<span class="plus" id="plus_{{ dogname}}">+</span>]</div>
           </div>
           <div class="dog_info" id="dog_info_{{ dogname }}">
           {% for kick in dog.kicks[-10:] %}
           <div class="kick">
           <span class="kick_date">{{ kick.0.ctime() }}</span> <span class="kick_ip">(from {{ kick.1 }})</span>
           </div>
           {% endfor %}
           </div>
           </div>
           {% endfor %}
        </div>
    </div>
    <footer id="page-footer">
        <div class="inner">
            <h5>2016 Justin Payne | Released into the public domain</h5>
        </div>
    </footer>
</div>
<script type="text/javascript">
function toggle_visibility(id) {
       var e = document.getElementById('dog_info_' + id);
       var s = document.getElementById('plus_' + id);
       if(e.style.display == 'block'){
          e.style.display = 'none';
          s.textContent = '+';
      } else {
          e.style.display = 'block';
          s.textContent = '-';
          }
    }
</script>
</BODY>
</HTML>
""")

app = Flask(__name__)

@app.route('/')
def main():
	return template.render(dogs=dogs, tag=tag)

@app.route('/help')
def help():
	print("help")
	return render_page()
	
	

class Dog(object):
	def __init__(self):
		self.kicks = []
		
	def kick(self, who_kicked='0.0.0.0'):
		if len(self.kicks) >= 11:
			self.kicks.pop(0)
		self.kicks.append((datetime.now(), who_kicked))
		return self
		
	@property
	def mean(self):
		'return mean time between kicks over 10-element sliding window'
		times = [d[0] for d in self.kicks]
		deltas = [times[i] - times[i-1] for i in range(1, len(times))]
		if deltas:
			return sum(deltas, timedelta()) / len(deltas) #need a zero delta to make sum() work
		return timedelta()
		
	@property
	def is_new(self):
		return len(self.kicks) < 11
		
	@property
	def is_expired(self):
		if self.kicks:
			return (datetime.now() - self.kicks[-1][0]) > self.mean * 2
		return False
			
dogs = defaultdict(Dog)
	
@app.route('/watch/<endpoint_name>')
def kick_the_dog(endpoint_name):
	me = request.remote_addr	
	dogs[endpoint_name].kick(me)
	return 'BARK', 204 #HTTP_NO_CONTENT
		
		
		
		
if __name__ == '__main__':
	class GoodDog(Dog):
		@property
		def is_new(self):
			return False
		@property
		def is_expired(self):
			return False
	class BadDog(GoodDog):
		@property
		def is_expired(self):
			return True
	dogs['test_dog_1'] = Dog().kick()
	dogs['test_good_dog'] = GoodDog().kick().kick().kick()
	dogs['test_bad_dog'] = BadDog().kick()
	app.run(debug=True)