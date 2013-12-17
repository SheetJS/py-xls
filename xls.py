#!/usr/bin/env python
import PyV8, base64

class MyConsole(PyV8.JSClass):
    def log(self, *args):
        print(" ".join([str(x) for x in args]))
    def error(self, *args):
        print >>stderr, " ".join([str(x) for x in args])

class GlobalContext(PyV8.JSClass):
    console = MyConsole()

class XLSSheet:
	def __init__(self, ws):
		self.ws = ws;


class XLSFile:
	def __init__(self, fname=None, b64=None):
		self._gc = GlobalContext();
		self.c = PyV8.JSContext(self._gc);
		self.c.enter();
		self.c.eval(xlsjscode);
		if fname is not None: self.readfile(fname);
		elif b64 is not None: self.readb64(b64);

	def sheetnames(self, idx=None):
		"""Returns an array of the sheet names"""
		if idx is None: return self.wb.SheetNames[:]
		return self.wb.SheetNames[idx]

	def sheet(self, idx_or_name):
		"""Returns a sheet object given an index or name"""
		if isinstance(idx_or_name, int):
			return self.sheet(self.sheetnames(idx_or_name));
		return XLSSheet(self.wb.Sheets[idx_or_name]);

	def readb64(self, b64):
		self.wb = self.c.locals['XLS'].read(b64, {'type': 'base64'});
		return self.wb;

	def readfile(self, fname):
		return self.readb64(base64.b64encode(open(fname, 'rb').read()));

	def csvify(self, sheet):
		return self.c.locals['XLS'].utils.sheet_to_csv(sheet.ws if isinstance(sheet, XLSSheet) else sheet);

class Utils():
	def __init__(self):
		self._gc = GlobalContext();
		self.c = PyV8.JSContext(self._gc);
		self.c.enter();
		self.c.eval(xlsjscode);
		self._utils = self.c.locals['XLS'].utils; 

	def csvify(self, sheet):
		return self._utils.sheet_to_csv(sheet.ws if isinstance(sheet, XLSSheet) else sheet);


xlsjscode="""
/* xls.js (C) 2013 SheetJS -- http://sheetjs.com */
/* vim: set ts=2: */
/*jshint eqnull:true, funcscope:true */
var XLS = {};
(function(XLS){
if(typeof module !== "undefined" && typeof require !== 'undefined') {
	if(typeof cptable === 'undefined') var cptable = require('codepage');
	var current_codepage = 1252, current_cptable = cptable[1252];
}
function reset_cp() {
	current_codepage = 1252; if(typeof cptable !== 'undefined') current_cptable = cptable[1252];
}
function _getchar(x) { return String.fromCharCode(x); }

/* Buffer.concat was added in the 0.8 series, so this is for older versions */
if(typeof Buffer !== "undefined" && !Buffer.concat)
Buffer.concat = function(list, length) {
	if (!Array.isArray(list)) {
		throw new TypeError('Usage: Buffer.concat(list, [length])');
	}

	if (list.length === 0) {
		return new Buffer(0);
	} else if (list.length === 1) {
		return list[0];
	}
	var i, buf;
	if (typeof length !== 'number') {
		length = 0;
		for (i = 0; i < list.length; i++) {
			buf = list[i];
			length += buf.length;
		}
	}

	var buffer = new Buffer(length);
	var pos = 0;
	for (i = 0; i < list.length; i++) {
		buf = list[i];
		buf.copy(buffer, pos);
		pos += buf.length;
	}
	return buffer;
};

var Buffers = Array;

function readIEEE754(buf, idx, isLE, nl, ml) {
	if(isLE === undefined) isLE = true;
	if(!nl) nl = 8;
	if(!ml && nl === 8) ml = 52;
	var e, m, el = nl * 8 - ml - 1, eMax = (1 << el) - 1, eBias = eMax >> 1;
	var bits = -7, d = isLE ? -1 : 1, i = isLE ? (nl - 1) : 0, s = buf[idx + i];

	i += d;
	e = s & ((1 << (-bits)) - 1); s >>>= (-bits); bits += el;
	for (; bits > 0; e = e * 256 + buf[idx + i], i += d, bits -= 8);
	m = e & ((1 << (-bits)) - 1); e >>>= (-bits); bits += ml;
	for (; bits > 0; m = m * 256 + buf[idx + i], i += d, bits -= 8);
	if (e === eMax) return m ? NaN : ((s ? -1 : 1) * Infinity);
	else if (e === 0) e = 1 - eBias;
	else { m = m + Math.pow(2, ml); e = e - eBias; }
	return (s ? -1 : 1) * m * Math.pow(2, e - ml);
}

var Base64 = (function(){
	var map = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";
	return {
		encode: function(input, utf8) {
			var o = "";
			var c1, c2, c3, e1, e2, e3, e4;
			for(var i = 0; i < input.length; ) {
				c1 = input.charCodeAt(i++);
				c2 = input.charCodeAt(i++);
				c3 = input.charCodeAt(i++);
				e1 = c1 >> 2;
				e2 = (c1 & 3) << 4 | c2 >> 4;
				e3 = (c2 & 15) << 2 | c3 >> 6;
				e4 = c3 & 63;
				if (isNaN(c2)) { e3 = e4 = 64; }
				else if (isNaN(c3)) { e4 = 64; }
				o += map.charAt(e1) + map.charAt(e2) + map.charAt(e3) + map.charAt(e4);
			}
			return o;
		},
		decode: function(input, utf8) {
			var o = "";
			var c1, c2, c3;
			var e1, e2, e3, e4;
			input = input.replace(/[^A-Za-z0-9\\+\\/\\=]/g, "");
			for(var i = 0; i < input.length;) {
				e1 = map.indexOf(input.charAt(i++));
				e2 = map.indexOf(input.charAt(i++));
				e3 = map.indexOf(input.charAt(i++));
				e4 = map.indexOf(input.charAt(i++));
				c1 = e1 << 2 | e2 >> 4;
				c2 = (e2 & 15) << 4 | e3 >> 2;
				c3 = (e3 & 3) << 6 | e4;
				o += String.fromCharCode(c1);
				if (e3 != 64) { o += String.fromCharCode(c2); }
				if (e4 != 64) { o += String.fromCharCode(c3); }
			}
			return o;
		}
	};
})();

function s2a(s) {
	if(typeof Buffer !== 'undefined') return new Buffer(s, "binary");
	var w = s.split("").map(function(x){ return x.charCodeAt(0) & 0xff; });
	return w;
}

if(typeof Buffer !== "undefined") {
	Buffer.prototype.hexlify= function() { return this.toString('hex'); };
	Buffer.prototype.utf16le= function(s,e){return this.toString('utf16le',s,e).replace(/\\u0000/,'').replace(/[\\u0001-\\u0006]/,'!');};
	Buffer.prototype.utf8 = function(s,e) { return this.toString('utf8',s,e); };
	Buffer.prototype.lpstr = function(i) { var len = this.readUInt32LE(i); return len > 0 ? this.utf8(i+4,i+4+len-1) : "";};
	Buffer.prototype.lpwstr = function(i) { var len = 2*this.readUInt32LE(i); return this.utf8(i+4,i+4+len-1);};
	if(typeof cptable !== "undefined") Buffer.prototype.lpstr = function(i) {
		var len = this.readUInt32LE(i);
		if(len === 0) return "";
		if(typeof current_cptable === "undefined") return this.utf8(i+4,i+4+len-1);
		var t = Array(this.slice(i+4,i+4+len-1));
		//1console.log("start", this.l, len, t);
		var c, j = i+4, o = "", cc;
		for(;j!=i+4+len;++j) {
			c = this.readUInt8(j);
			cc = current_cptable.dec[c];
			if(typeof cc === 'undefined') {
				c = c*256 + this.readUInt8(++j);
				cc = current_cptable.dec[c];
			}
			if(typeof cc === 'undefined') throw "Unrecognized character " + c.toString(16);
			if(c === 0) break;
			o += cc;
		//1console.log(cc, cc.charCodeAt(0), o, this.l);
		}
		return o;
	};
}

Array.prototype.readUInt8 = function(idx) { return this[idx]; };
Array.prototype.readUInt16LE = function(idx) { return this[idx+1]*(1<<8)+this[idx]; };
Array.prototype.readInt16LE = function(idx) { var u = this.readUInt16LE(idx); if(!(u & 0x8000)) return u; return (0xffff - u + 1) * -1; };
Array.prototype.readUInt32LE = function(idx) { return this[idx+3]*(1<<24)+this[idx+2]*(1<<16)+this[idx+1]*(1<<8)+this[idx]; };
Array.prototype.readInt32LE = function(idx) { var u = this.readUInt32LE(idx); if(!(u & 0x80000000)) return u; return (0xffffffff - u + 1) * -1; };
Array.prototype.readDoubleLE = function(idx) { return readIEEE754(this, idx||0);};

Array.prototype.hexlify = function() { return this.map(function(x){return (x<16?"0":"") + x.toString(16);}).join(""); };

Array.prototype.utf16le = function(s,e) { var str = ""; for(var i=s; i<e; i+=2) str += String.fromCharCode(this.readUInt16LE(i)); return str.replace(/\\u0000/,'').replace(/[\\u0001-\\u0006]/,'!'); };

Array.prototype.utf8 = function(s,e) { var str = ""; for(var i=s; i<e; i++) str += String.fromCharCode(this.readUInt8(i)); return str; };

Array.prototype.lpstr = function(i) { var len = this.readUInt32LE(i); return len > 0 ? this.utf8(i+4,i+4+len-1) : "";};
Array.prototype.lpwstr = function(i) { var len = 2*this.readUInt32LE(i); return this.utf8(i+4,i+4+len-1);};

function bconcat(bufs) { return (typeof Buffer !== 'undefined') ? Buffer.concat(bufs) : [].concat.apply([], bufs); }

function ReadShift(size, t) {
	var o, w, vv, i, loc; t = t || 'u';
	if(size === 'ieee754') { size = 8; t = 'f'; }
	switch(size) {
		case 1: o = this.readUInt8(this.l); break;
		case 2: o=t==='u'?this.readUInt16LE(this.l):this.readInt16LE(this.l);break;
		case 4: o = this.readUInt32LE(this.l); break;
		case 8: if(t === 'f') { o = this.readDoubleLE(this.l); break; }
		/* falls through */
		case 16: o = this.toString('hex', this.l,this.l+size); break;

		case 'utf8': size = t; o = this.utf8(this.l, this.l + size); break;
		case 'utf16le': size = 2*t; o = this.utf16le(this.l, this.l + size); break;

		/* [MS-OLEDS] 2.1.4 LengthPrefixedAnsiString */
		case 'lpstr': o = this.lpstr(this.l); size = 5 + o.length; break;

		case 'lpwstr': o = this.lpwstr(this.l); size = 5 + o.length; if(o[o.length-1] == '\\u0000') size += 2; break;

		/* sbcs and dbcs support continue records in the SST way TODO codepages */
		/* TODO: DBCS http://msdn.microsoft.com/en-us/library/cc194788.aspx */
		case 'dbcs': size = 2*t; o = ""; loc = this.l;
			for(i = 0; i != t; ++i) {
				if(this.lens && this.lens.indexOf(loc) !== -1) {
					w = this.readUInt8(loc);
					this.l = loc + 1;
					vv = ReadShift.call(this, w ? 'dbcs' : 'sbcs', t-i);
					return o + vv;
				}
				o += _getchar(this.readUInt16LE(loc));
				loc+=2;
			} break;

		case 'sbcs': size = t; o = ""; loc = this.l;
			for(i = 0; i != t; ++i) {
				if(this.lens && this.lens.indexOf(loc) !== -1) {
					w = this.readUInt8(loc);
					this.l = loc + 1;
					vv = ReadShift.call(this, w ? 'dbcs' : 'sbcs', t-i);
					return o + vv;
				}
				o += _getchar(this.readUInt8(loc));
				loc+=1;
			} break;

		case 'cstr': size = 0; o = "";
			while((w=this.readUInt8(this.l + size++))!==0) o+= _getchar(w);
			break;
		case 'wstr': size = 0; o = "";
			while((w=this.readUInt16LE(this.l +size))!==0){o+= _getchar(w);size+=2;}
			size+=2; break;
	}
	this.l+=size; return o;
}

function CheckField(hexstr, fld) {
	var m = this.slice(this.l, this.l+hexstr.length/2).hexlify('hex');
	if(m !== hexstr) throw (fld||"") + 'Expected ' + hexstr + ' saw ' + m;
	this.l += hexstr.length/2;
}

function WarnField(hexstr, fld) {
	var m = this.slice(this.l, this.l+hexstr.length/2).hexlify('hex');
	if(m !== hexstr) console.error((fld||"") + 'Expected ' + hexstr +' saw ' + m);
	this.l += hexstr.length/2;
}

function prep_blob(blob, pos) {
	blob.read_shift = ReadShift.bind(blob);
	blob.chk = CheckField;
	blob.l = pos || 0;
	var read = ReadShift.bind(blob), chk = CheckField.bind(blob);
	return [read, chk];
}

/* Spreadsheet Format */
var SSF = (function() {
	var SSF = {};
String.prototype.reverse=function(){return this.split("").reverse().join("");};
var _strrev = function(x) { return String(x).reverse(); };
function fill(c,l) { return new Array(l+1).join(c); }
function pad(v,d){var t=String(v);return t.length>=d?t:(fill(0,d-t.length)+t);}
/* Options */
var opts_fmt = {};
function fixopts(o){for(var y in opts_fmt) if(o[y]===undefined) o[y]=opts_fmt[y];}
SSF.opts = opts_fmt;
opts_fmt.date1904 = 0;
opts_fmt.output = "";
opts_fmt.mode = "";
var table_fmt = {
	1:  '0',
	2:  '0.00',
	3:  '#,##0',
	4:  '#,##0.00',
	9:  '0%',
	10: '0.00%',
	11: '0.00E+00',
	12: '# ?/?',
	13: '# ??/??',
	14: 'mm/dd/yy',
	15: 'd-mmm-yy',
	16: 'd-mmm',
	17: 'mmm-yy',
	18: 'h:mm AM/PM',
	19: 'h:mm:ss AM/PM',
	20: 'h:mm',
	21: 'h:mm:ss',
	22: 'm/d/yy h:mm',
	37: '#,##0 ;(#,##0)',
	38: '#,##0 ;[Red](#,##0)',
	39: '#,##0.00;(#,##0.00)',
	40: '#,##0.00;[Red](#,##0.00)',
	45: 'mm:ss',
	46: '[h]:mm:ss',
	47: 'mmss.0',
	48: '##0.0E+0',
	49: '@'
};
var days = [
	['Sun', 'Sunday'],
	['Mon', 'Monday'],
	['Tue', 'Tuesday'],
	['Wed', 'Wednesday'],
	['Thu', 'Thursday'],
	['Fri', 'Friday'],
	['Sat', 'Saturday']
];
var months = [
	['J', 'Jan', 'January'],
	['F', 'Feb', 'February'],
	['M', 'Mar', 'March'],
	['A', 'Apr', 'April'],
	['M', 'May', 'May'],
	['J', 'Jun', 'June'],
	['J', 'Jul', 'July'],
	['A', 'Aug', 'August'],
	['S', 'Sep', 'September'],
	['O', 'Oct', 'October'],
	['N', 'Nov', 'November'],
	['D', 'Dec', 'December']
];
var general_fmt = function(v) {
	if(typeof v === 'boolean') return v ? "TRUE" : "FALSE";
};
SSF._general = general_fmt;
var parse_date_code = function parse_date_code(v,opts) {
	var date = Math.floor(v), time = Math.round(86400 * (v - date)), dow=0;
	var dout=[], out={D:date, T:time}; fixopts(opts = (opts||{}));
	if(opts.date1904) date += 1462;
	if(date === 60) {dout = [1900,2,29]; dow=3;}
	else {
		if(date > 60) --date;
		/* 1 = Jan 1 1900 */
		var d = new Date(1900,0,1);
		d.setDate(d.getDate() + date - 1);
		dout = [d.getFullYear(), d.getMonth()+1,d.getDate()];
		dow = d.getDay();
		if(opts.mode === 'excel' && date < 60) dow = (dow + 6) % 7;
	}
	out.y = dout[0]; out.m = dout[1]; out.d = dout[2];
	out.S = time % 60; time = Math.floor(time / 60);
	out.M = time % 60; time = Math.floor(time / 60);
	out.H = time;
	out.q = dow;
	return out;
};
SSF.parse_date_code = parse_date_code;
var write_date = function(type, fmt, val) {
	switch(type) {
		case 'y': switch(fmt) { /* year */
			case 'y': case 'yy': return pad(val.y % 100,2);
			default: return val.y;
		} break;
		case 'm': switch(fmt) { /* month */
			case 'm': return val.m;
			case 'mm': return pad(val.m,2);
			case 'mmm': return months[val.m-1][1];
			case 'mmmm': return months[val.m-1][2];
			case 'mmmmm': return months[val.m-1][0];
			default: throw 'bad month format: ' + fmt;
		} break;
		case 'd': switch(fmt) { /* day */
			case 'd': return val.d;
			case 'dd': return pad(val.d,2);
			case 'ddd': return days[val.q][0];
			case 'dddd': return days[val.q][1];
			default: throw 'bad day format: ' + fmt;
		} break;
		case 'h': switch(fmt) { /* 12-hour */
			case 'h': return 1+(val.H+11)%12;
			case 'hh': return pad(1+(val.H+11)%12, 2);
			default: throw 'bad hour format: ' + fmt;
		} break;
		case 'H': switch(fmt) { /* 24-hour */
			case 'h': return val.H;
			case 'hh': return pad(val.H, 2);
			default: throw 'bad hour format: ' + fmt;
		} break;
		case 'M': switch(fmt) { /* minutes */
			case 'm': return val.M;
			case 'mm': return pad(val.M, 2);
			default: throw 'bad minute format: ' + fmt;
		} break;
		case 's': switch(fmt) { /* seconds */
			case 's': return val.S;
			case 'ss': return pad(val.S, 2);
			default: throw 'bad second format: ' + fmt;
		} break;
		/* TODO: handle the ECMA spec format ee -> yy */
		case 'e': { return val.y; } break;
		case 'A': return (val.h>=12 ? 'P' : 'A') + fmt.substr(1);
		default: throw 'bad format type ' + type + ' in ' + fmt;
	}
};
function split_fmt(fmt) {
	return fmt.reverse().split(/;(?!\\\\)/).reverse().map(_strrev);
}
SSF._split = split_fmt;
function eval_fmt(fmt, v, opts) {
	var out = [], o = "", i = 0, c = "", lst='t', q = {}, dt;
	fixopts(opts = (opts || {}));
	var hr='H';
	/* Tokenize */
	while(i < fmt.length) {
		switch((c = fmt[i])) {
			case '"': /* Literal text */
				for(o="";fmt[++i] !== '"';) o += fmt[(fmt[i] === '\\\\' ? ++i : i)];
				out.push({t:'t', v:o}); break;
			case '\\\\': out.push({t:'t', v:fmt[++i]}); ++i; break;
			case '@': /* Text Placeholder */
				out.push({t:'T', v:v}); ++i; break;
			/* Dates */
			case 'm': case 'd': case 'y': case 'h': case 's': case 'e':
				if(!dt) dt = parse_date_code(v, opts);
				o = fmt[i]; while(fmt[++i] === c) o+=c;
				if(c === 'm' && lst.toLowerCase() === 'h') c = 'M'; /* m = minute */
				if(c === 'h') c = hr;
				q={t:c, v:o}; out.push(q); lst = c; break;
			case 'A':
				q={t:c,v:"A"};
				if(fmt.substr(i, 3) === "A/P") {hr = 'h'; i+=3;}
				else if(fmt.substr(i,5) === "AM/PM") { q.v = "AM"; i+=5; hr = 'h'; }
				else q.t = "t";
				out.push(q); lst = c; break;
			case '[': /* TODO: Fix this -- ignore all conditionals and formatting */
				while(fmt[i++] !== ']'); break;
			default:
				if("$-+/():!^&'~{}<>= ".indexOf(c) === -1)
					throw 'unrecognized character ' + fmt[i] + ' in ' + fmt;
				out.push({t:'t', v:c}); ++i; break;
		}
	}
	/* walk backwards */
	for(i=out.length-1, lst='t'; i >= 0; --i) {
		switch(out[i].t) {
			case 'h': case 'H': out[i].t = hr; lst='h'; break;
			case 'd': case 'y': case 's': case 'M': case 'e': lst=out[i].t; break;
			case 'm': if(lst === 's') out[i].t = 'M'; break;

		}
	}

	/* replace fields */
	for(i=0; i < out.length; ++i) {
		switch(out[i].t) {
			case 't': case 'T': break;
			case 'd': case 'm': case 'y': case 'h': case 'H': case 'M': case 's': case 'A': case 'e':
				out[i].v = write_date(out[i].t, out[i].v, dt);
				out[i].t = 't'; break;
			default: throw "unrecognized type " + out[i].t;
		}
	}

	return out.map(function(x){return x.v;}).join("");
}
SSF._eval = eval_fmt;
function choose_fmt(fmt, v) {
	if(typeof fmt === "string") fmt = split_fmt(fmt);
	if(typeof v !== "number") return fmt[3];
	return v > 0 ? fmt[0] : v < 0 ? fmt[1] : fmt[2];
}

var format = function format(fmt,v,o) {
	fixopts(o = (o||{}));
	if(fmt === 0) return general_fmt(v, o);
	if(typeof fmt === 'number') fmt = table_fmt[fmt];
	var f = choose_fmt(fmt, v, o);
	return eval_fmt(f, v, o);
};

SSF._choose = choose_fmt;
SSF._table = table_fmt;
SSF.load = function(fmt, idx) { table_fmt[idx] = fmt; };
SSF.format = format;

	return SSF;
})();
/* [MS-OLEPS] v20130118 */
/* [MS-OSHARED] v20130211 */

/* [MS-OLEPS] 2.2 PropertyType */
{
	var VT_EMPTY    = 0x0000;
	var VT_NULL     = 0x0001;
	var VT_I2       = 0x0002;
	var VT_I4       = 0x0003;
	var VT_R4       = 0x0004;
	var VT_R8       = 0x0005;
	var VT_CY       = 0x0006;
	var VT_DATE     = 0x0007;
	var VT_BSTR     = 0x0008;
	var VT_ERROR    = 0x000A;
	var VT_BOOL     = 0x000B;
	var VT_VARIANT  = 0x000C;
	var VT_DECIMAL  = 0x000E;
	var VT_I1       = 0x0010;
	var VT_UI1      = 0x0011;
	var VT_UI2      = 0x0012;
	var VT_UI4      = 0x0013;
	var VT_I8       = 0x0014;
	var VT_UI8      = 0x0015;
	var VT_INT      = 0x0016;
	var VT_UINT     = 0x0017;
	var VT_LPSTR    = 0x001E;
	var VT_LPWSTR   = 0x001F;
	var VT_FILETIME = 0x0040;
	var VT_BLOB     = 0x0041;
	var VT_STREAM   = 0x0042;
	var VT_STORAGE  = 0x0043;
	var VT_STREAMED_Object  = 0x0044;
	var VT_STORED_Object    = 0x0045;
	var VT_BLOB_Object      = 0x0046;
	var VT_CF       = 0x0047;
	var VT_CLSID    = 0x0048;
	var VT_VERSIONED_STREAM = 0x0049;
	var VT_VECTOR   = 0x1000;
	var VT_ARRAY    = 0x2000;

	var VT_STRING   = 0x0050; // 2.3.3.1.11 VtString
	var VT_USTR     = 0x0051; // 2.3.3.1.12 VtUnalignedString
	var VT_CUSTOM   = [VT_STRING, VT_USTR];
}

/* [MS-OSHARED] 2.3.3.2.2.1 Document Summary Information PIDDSI */
var DocSummaryPIDDSI = {
	0x01: { n: 'CodePage', t: VT_I2 },
	0x02: { n: 'Category', t: VT_STRING },
	0x03: { n: 'PresentationFormat', t: VT_STRING },
	0x04: { n: 'ByteCount', t: VT_I4 },
	0x05: { n: 'LineCount', t: VT_I4 },
	0x06: { n: 'ParagraphCount', t: VT_I4 },
	0x07: { n: 'SlideCount', t: VT_I4 },
	0x08: { n: 'NoteCount', t: VT_I4 },
	0x09: { n: 'HiddenCount', t: VT_I4 },
	0x0a: { n: 'MultimediaClipCount', t: VT_I4 },
	0x0b: { n: 'Scale', t: VT_BOOL },
	0x0c: { n: 'HeadingPair', t: VT_VECTOR | VT_VARIANT },
	0x0d: { n: 'DocParts', t: VT_VECTOR | VT_LPSTR },
	0x0e: { n: 'Manager', t: VT_STRING },
	0x0f: { n: 'Company', t: VT_STRING },
	0x10: { n: 'LinksDirty', t: VT_BOOL },
	0x11: { n: 'CharacterCount', t: VT_I4 },
	0x13: { n: 'SharedDoc', t: VT_BOOL },
	0x16: { n: 'HLinksChanged', t: VT_BOOL },
	0x17: { n: 'Version', t: VT_I4 },
	0xFF: {}
};

/* [MS-OSHARED] 2.3.3.2.1.1 Summary Information Property Set PIDSI */
var SummaryPIDSI = {
	0x01: { n: 'CodePage', t: VT_I2 },
	0x02: { n: 'Title', t: VT_STRING },
	0x03: { n: 'Subject', t: VT_STRING },
	0x04: { n: 'Author', t: VT_STRING },
	0x05: { n: 'Keywords', t: VT_STRING },
	0x06: { n: 'Comments', t: VT_STRING },
	0x07: { n: 'Template', t: VT_STRING },
	0x08: { n: 'LastAuthor', t: VT_STRING },
	0x09: { n: 'RevNumber', t: VT_STRING },
	0x0A: { n: 'EditTime', t: VT_FILETIME },
	0x0B: { n: 'LastPrinted', t: VT_FILETIME },
	0x0C: { n: 'CreateTime', t: VT_FILETIME },
	0x0D: { n: 'SaveTime', t: VT_FILETIME },
	0x0E: { n: 'PageCount', t: VT_I4 },
	0x0F: { n: 'WordCount', t: VT_I4 },
	0x10: { n: 'CharCount', t: VT_I4 },
	0x11: { n: 'Thumbnail', t: VT_CF },
	0x12: { n: 'ApplicationName', t: VT_LPSTR },
	0x13: { n: 'DocumentSecurity', t: VT_I4 },
	0xFF: {}
};

/* [MS-OLEPS] 2.18 */
var SpecialProperties = {
	0x80000000: { n: 'Locale', t: VT_UI4 },
	0x80000003: { n: 'Behavior', t: VT_UI4 },
	0x69696969: {}
};

(function() {
	for(var y in SpecialProperties) if(SpecialProperties.hasOwnProperty(y))
	DocSummaryPIDDSI[y] = SummaryPIDSI[y] = SpecialProperties[y];
})();

/* [MS-DTYP] 2.3.1 FILETIME */
/* [MS-OLEDS] 2.1.3 FILETIME (Packet Version) */
/* [MS-OLEPS] 2.8 FILETIME (Packet Version) */
function parse_FILETIME(blob) {
	var read = ReadShift.bind(blob), chk = CheckField.bind(blob);
	var dwLowDateTime = read(4), dwHighDateTime = read(4);
	return [dwLowDateTime, dwHighDateTime];
}

/* [MS-OSHARED] 2.3.3.1.4 Lpstr */
function parse_lpstr(blob, type, pad) {
	var read = ReadShift.bind(blob), chk = CheckField.bind(blob);
	var str = read('lpstr');
	if(pad) blob.l += (4 - ((str.length+1) % 4)) % 4;
	return str;
}

/* [MS-OSHARED] 2.3.3.1.6 Lpwstr */
function parse_lpwstr(blob, type, pad) {
	var read = ReadShift.bind(blob), chk = CheckField.bind(blob);
	var str = read('lpwstr');
	if(pad) blob.l += (4 - ((str.length+1) % 4)) % 4;
	return str;
}


/* [MS-OSHARED] 2.3.3.1.11 VtString */
/* [MS-OSHARED] 2.3.3.1.12 VtUnalignedString */
function parse_VtStringBase(blob, stringType, pad) {
	if(stringType) switch(stringType) {
		case VT_LPSTR: return parse_lpstr(blob, stringType, pad);
		case VT_LPWSTR: return parse_lpwstr(blob);
		default: throw "Unrecognized string type " + stringType;
	}
	else return parse_VtStringBase(blob, blob.read_shift(2), pad);
}

function parse_VtString(blob, t, pad) { return parse_VtStringBase(blob, t, 4); }
function parse_VtUnalignedString(blob, t) { if(!t) throw new Error("dafuq?"); return parse_VtStringBase(blob, t, 0); }

/* [MS-OSHARED] 2.3.3.1.9 VtVecUnalignedLpstrValue */
function parse_VtVecUnalignedLpstrValue(blob) {
	var read = ReadShift.bind(blob), chk = CheckField.bind(blob);
	var length = read(4);
	var ret = [];
	for(var i = 0; i != length; ++i) ret[i] = read('lpstr');
	return ret;
}

/* [MS-OSHARED] 2.3.3.1.10 VtVecUnalignedLpstr */
function parse_VtVecUnalignedLpstr(blob) {
	return parse_VtVecUnalignedLpstrValue(blob);
}

/* [MS-OSHARED] 2.3.3.1.13 VtHeadingPair */
function parse_VtHeadingPair(blob) {
	var headingString = parse_TypedPropertyValue(blob, VT_USTR);
	var headerParts = parse_TypedPropertyValue(blob, VT_I4);
	return [headingString, headerParts];
}

/* [MS-OSHARED] 2.3.3.1.14 VtVecHeadingPairValue */
function parse_VtVecHeadingPairValue(blob) {
	var cElements = blob.read_shift(4);
	var out = [];
	for(var i = 0; i != cElements / 2; ++i) out.push(parse_VtHeadingPair(blob));
	return out;
}

/* [MS-OSHARED] 2.3.3.1.15 VtVecHeadingPair */
function parse_VtVecHeadingPair(blob) {
	// NOTE: When invoked, wType & padding were already consumed
	return parse_VtVecHeadingPairValue(blob);
}

/* [MS-OLEPS] 2.18.1 Dictionary (uses 2.17, 2.16) */
function parse_dictionary(blob,CodePage) {
	var read = ReadShift.bind(blob), chk = CheckField.bind(blob);
	var cnt = read(4);
	var dict = {};
	for(var j = 0; j != cnt; ++j) {
		var pid = read(4);
		var len = read(4);
		dict[pid] = read((CodePage === 0x4B0 ?'utf16le':'utf8'), len).replace(/\\u0000/g,'').replace(/[\\u0001-\\u0006]/g,'!');
	}
	if(blob.l % 4) blob.l = (blob.l>>2+1)<<2;
	return dict;
}

/* [MS-OLEPS] 2.9 BLOB */
function parse_BLOB(blob) {
	var size = blob.read_shift(4);
	var bytes = blob.slice(blob.l,blob.l+size);
	if(blob.l % 4) blob.l += (4 - (blob.l % 4)) % 4;
	return bytes;
}

/* [MS-OLEPS] 2.11 ClipboardData */
function parse_ClipboardData(blob) {
	// TODO
	var o = {};
	o.Size = blob.read_shift(4);
	//o.Format = blob.read_shift(4);
	blob.l += o.Size;
	return o;
}

/* [MS-OLEPS] 2.14 Vector and Array Property Types */
function parse_VtVector(blob, cb) {
	/* [MS-OLEPS] 2.14.2 VectorHeader */
	var Length = blob.read_shift(4);
	var o = [];
	for(var i = 0; i != Length; ++i) {
		o.push(cb(blob));
	}
	return o;
}

/* [MS-OLEPS] 2.15 TypedPropertyValue */
function parse_TypedPropertyValue(blob, type) {
	var read = ReadShift.bind(blob), chk = CheckField.bind(blob);
	var t = read(2), ret;
	read(2);
	if(type !== VT_VARIANT)
	if(t !== type && VT_CUSTOM.indexOf(type)===-1) throw new Error('Expected type ' + type + ' saw ' + t);
	switch(type === VT_VARIANT ? t : type) {
		case VT_I2: ret = read(2, 'i'); read(2); return ret;
		case VT_I4: ret = read(4, 'i'); return ret;
		case VT_BOOL: return read(4) !== 0x0;
		case VT_UI4: ret = read(4); return ret;
		case VT_LPSTR: return parse_lpstr(blob, t, 4).replace(/\\u0000/g,'');
		case VT_LPWSTR: return parse_lpwstr(blob);
		case VT_FILETIME: return parse_FILETIME(blob);
		case VT_BLOB: return parse_BLOB(blob);
		case VT_CF: return parse_ClipboardData(blob);
		case VT_STRING: return parse_VtString(blob, t, 4).replace(/\\u0000/g,'');
		case VT_USTR: return parse_VtUnalignedString(blob, t, 4).replace(/\\u0000/g,'');
		case VT_VECTOR | VT_VARIANT: return parse_VtVecHeadingPair(blob);
		case VT_VECTOR | VT_LPSTR: return parse_VtVecUnalignedLpstr(blob);
		default: throw new Error("TypedPropertyValue unrecognized type " + type + " " + t);
	}
}
function parse_VTVectorVariant(blob) {
	/* [MS-OLEPS] 2.14.2 VectorHeader */
	var Length = blob.read_shift(4);

	if(Length % 2 !== 0) throw new Error("VectorHeader Length=" + Length + " must be even");
	var o = [];
	for(var i = 0; i != Length; ++i) {
		o.push(parse_TypedPropertyValue(blob, VT_VARIANT));
	}
	return o;
}

/* [MS-OLEPS] 2.20 PropertySet */
function parse_PropertySet(blob, PIDSI) {
	var start_addr = blob.l;
	var read = ReadShift.bind(blob), chk = CheckField.bind(blob);
	var size = read(4);
	var NumProps = read(4);
	var Props = [], i = 0;
	var CodePage = 0;
	var Dictionary = -1, DictObj;
	for(i = 0; i != NumProps; ++i) {
		var PropID = read(4);
		var Offset = read(4);
		Props[i] = [PropID, Offset + start_addr];
	}
	var PropH = {};
	for(i = 0; i != NumProps; ++i) {
		if(blob.l !== Props[i][1]) {
			throw new Error("Read Error: Expected address " + Props[i][1] + ' at ' + blob.l + ' :' + i);
		}
		if(PIDSI) {
			var piddsi = PIDSI[Props[i][0]];
			PropH[piddsi.n] = parse_TypedPropertyValue(blob, piddsi.t);
			if(piddsi.n == "CodePage") switch(PropH[piddsi.n]) {
				/* TODO: Generate files under every codepage */
				case 10000: break; // OSX Roman
				case 1252: break; // Windows Latin

				case 874: // SB Windows Thai
				case 1250: // SB Windows Central Europe
				case 1251: // SB Windows Cyrillic
				case 1253: // SB Windows Greek
				case 1254: // SB Windows Turkish
				case 1255: // SB Windows Hebrew
				case 1256: // SB Windows Arabic

				case 932: // DB Windows Japanese Shift-JIS
				case 936: // DB Windows Simplified Chinese GBK
				case 949: // DB Windows Korean
				case 950: // DB Windows Traditional Chinese Big5

				case 1200: // UTF16LE
				case 1201: // UTF16BE
				case 65000: case -536: // UTF-7
				case 65001: case -535: // UTF-8
					break;
				default: throw new Error("Unsupported CodePage: " + PropH[piddsi.n]);
			}
		} else {
			if(Props[i][0] === 0x1) {
				CodePage = PropH.CodePage = parse_TypedPropertyValue(blob, VT_I2);
				if(Dictionary !== -1) {
					var oldpos = blob.l;
					blob.l = Props[Dictionary][1];
					DictObj = parse_dictionary(blob,CodePage);
					blob.l = oldpos;
				}
			} else if(Props[i][0] === 0) {
				if(CodePage === 0) { Dictionary = i; blob.l = Props[i+1][1]; continue; }
				DictObj = parse_dictionary(blob,CodePage);
			} else {
				var name = DictObj[Props[i][0]];
				var val;
				/* [MS-OSHARED] 2.3.3.2.3.1.2 + PROPVARIANT */
				switch(blob[blob.l]) {
					case VT_BLOB: blob.l += 4; val = parse_BLOB(blob); break;
					case VT_LPSTR: blob.l += 4; val = parse_VtString(blob, blob[blob.l-4]); break;
					case VT_LPWSTR: blob.l += 4; val = parse_VtString(blob, blob[blob.l-4]); break;
					case VT_I4: blob.l += 4; val = read(4, 'i'); break;
					case VT_UI4: blob.l += 4; val = read(4); break;
					case VT_R8: blob.l += 4; val = read(8, 'f'); break;
					case VT_BOOL: blob.l += 4; val = parsebool(blob, 4); break;
					case VT_FILETIME: blob.l += 4; val = parse_FILETIME(blob); break;
					default: throw new Error("unparsed value: " + blob[blob.l]);
				}
				PropH[name] = val;
			}
		}
	}
	blob.l = start_addr + size; /* step ahead to skip padding */
	return PropH;
}

/* [MS-OLEPS] 2.21 PropertySetStream */
function parse_PropertySetStream(file, PIDSI) {
	var blob = file.content;
	prep_blob(blob);
	var read = ReadShift.bind(blob), chk = CheckField.bind(blob);

	var NumSets, FMTID0, FMTID1, Offset0, Offset1;
	chk('feff', 'Byte Order: ');

	var vers = read(2); // TODO: check version
	var SystemIdentifier = read(4);
	chk(HEADER_CLSID, 'CLSID: ');
	NumSets = read(4);
	if(NumSets !== 1 && NumSets !== 2) throw "Unrecognized #Sets: " + NumSets;
	FMTID0 = read(16); Offset0 = read(4);

	if(NumSets === 1 && Offset0 !== blob.l) throw "Length mismatch";
	else if(NumSets === 2) { FMTID1 = read(16); Offset1 = read(4); }
	var PSet0 = parse_PropertySet(blob, PIDSI);

	var rval = { SystemIdentifier: SystemIdentifier };
	for(var y in PSet0) rval[y] = PSet0[y];
	//rval.blob = blob;
	rval.FMTID = FMTID0;
	//rval.PSet0 = PSet0;
	if(NumSets === 1) return rval;
	var PSet1 = parse_PropertySet(blob, null);
	for(y in PSet1) rval[y] = PSet1[y];
	rval.FMTID = [FMTID0, FMTID1]; // TODO: verify FMTID0/1
	return rval;
}
/* [MS-CFB] v20130118 */
if(typeof module !== "undefined" && typeof require !== 'undefined') CFB = require('cfb');
else var CFB = (function(){
var exports = {};
function parse(file) {


var mver = 3; // major version
var ssz = 512; // sector size
var mssz = 64; // mini sector size
var nds = 0; // number of directory sectors
var nfs = 0; // number of FAT sectors
var nmfs = 0; // number of mini FAT sectors
var ndfs = 0; // number of DIFAT sectors
var dir_start = 0; // first directory sector location
var minifat_start = 0; // first mini FAT sector location
var difat_start = 0; // first mini FAT sector location

var ms_cutoff_size = 4096; // mini stream cutoff size
var minifat_store = 0; // first sector with minifat data
var minifat_size = 0; // size of minifat data

var fat_addrs = []; // locations of FAT sectors

/* [MS-CFB] 2.2 Compound File Header */
var blob = file.slice(0,512);
prep_blob(blob);
var read = ReadShift.bind(blob), chk = CheckField.bind(blob);
//var wrn = WarnField.bind(blob);
var j = 0, q;

// header signature 8
chk(HEADER_SIGNATURE, 'Header Signature: ');

// clsid 16
chk(HEADER_CLSID, 'CLSID: ');

// minor version 2
//wrn(HEADER_MINOR_VERSION, 'Minor Version: ');
read(2);

// major version 3
mver = read(2);
switch(mver) {
	case 3: ssz = 512; break;
	case 4: ssz = 4096; break;
	default: throw "Major Version: Expected 3 or 4 saw " + mver;
}

// reprocess header
var pos = blob.l;
blob = file.slice(0,ssz);
prep_blob(blob,pos);
read = ReadShift.bind(blob);
chk = CheckField.bind(blob);
var header = file.slice(0,ssz);

// Byte Order TODO
chk('feff', 'Byte Order: ');

// Sector Shift
switch((q = read(2))) {
	case 0x09: if(mver !== 3) throw 'MajorVersion/SectorShift Mismatch'; break;
	case 0x0c: if(mver !== 4) throw 'MajorVersion/SectorShift Mismatch'; break;
	default: throw 'Sector Shift: Expected 9 or 12 saw ' + q;
}

// Mini Sector Shift
chk('0600', 'Mini Sector Shift: ');

// Reserved
chk('000000000000', 'Mini Sector Shift: ');

// Number of Directory Sectors
nds = read(4);
if(mver === 3 && nds !== 0) throw '# Directory Sectors: Expected 0 saw ' + nds;

// Number of FAT Sectors
nfs = read(4);

// First Directory Sector Location
dir_start = read(4);

// Transaction Signature TODO
read(4);

// Mini Stream Cutoff Size TODO
chk('00100000', 'Mini Stream Cutoff Size: ');

// First Mini FAT Sector Location
minifat_start = read(4);

// Number of Mini FAT Sectors
nmfs = read(4);

// First DIFAT sector location
difat_start = read(4);

// Number of DIFAT Sectors
ndfs = read(4);

// Grab FAT Sector Locations
for(j = 0; blob.l != 512; ) {
	if((q = read(4))>=MAXREGSECT) break;
	fat_addrs[j++] = q;
}


/** Break the file up into sectors */
var nsectors = Math.ceil((file.length - ssz)/ssz);
var sectors = [];
for(var i=1; i != nsectors; ++i) sectors[i-1] = file.slice(i*ssz,(i+1)*ssz);
sectors[nsectors-1] = file.slice(nsectors*ssz);

/** Chase down the rest of the DIFAT chain to build a comprehensive list
    DIFAT chains by storing the next sector number as the last 32 bytes */
function sleuth_fat(idx, cnt) {
	if(idx === ENDOFCHAIN) {
		if(cnt !== 0) throw "DIFAT chain shorter than expected";
		return;
	}
	if(idx !== FREESECT) {
		var sector = sectors[idx];
		for(var i = 0; i != ssz/4-1; ++i) {
			if((q = sector.readUInt32LE(i*4)) === ENDOFCHAIN) break;
			fat_addrs.push(q);
		}
		sleuth_fat(sector.readUInt32LE(ssz-4),cnt - 1);
	}
}
sleuth_fat(difat_start, ndfs);

/** DONT CAT THE FAT!  Just calculate where we need to go */
function get_buffer(byte_addr, bytes) {
	var addr = fat_addrs[Math.floor(byte_addr*4/ssz)];
	if(ssz - (byte_addr*4 % ssz) < (bytes || 0))
		throw "FAT boundary crossed: " + byte_addr + " "+bytes+" "+ssz;
	return sectors[addr].slice((byte_addr*4 % ssz));
}

function get_buffer_u32(byte_addr) {
	return get_buffer(byte_addr,4).readUInt32LE(0);
}

function get_next_sector(idx) { return get_buffer_u32(idx); }

/** Chains */
var chkd = new Array(sectors.length), sector_list = [];
var get_sector = function get_sector(k) { return sectors[k]; };
for(i=0; i != sectors.length; ++i) {
	var buf = [], k = (i + dir_start) % sectors.length;
	if(chkd[k]) continue;
	for(j=k; j<=MAXREGSECT; buf.push(j),j=get_next_sector(j)) chkd[j] = true;
	sector_list[k] = {nodes: buf};
	sector_list[k].data = Buffers(buf.map(get_sector)).toBuffer();
}
sector_list[dir_start].name = "!Directory";
if(nmfs > 0 && minifat_start !== ENDOFCHAIN) sector_list[minifat_start].name = "!MiniFAT";
sector_list[fat_addrs[0]].name = "!FAT";

/* [MS-CFB] 2.6.1 Compound File Directory Entry */
var files = {}, Paths = [], FileIndex = [], FullPaths = [], FullPathDir = {};
function read_directory(idx) {
	var blob, read, w;
	var sector = sector_list[idx].data;
	for(var i = 0; i != sector.length; i+= 128) {
		blob = sector.slice(i, i+128);
		prep_blob(blob, 64);
		read = ReadShift.bind(blob);
		var namelen = read(2);
		if(namelen === 0) return;
		var name = blob.utf16le(0,namelen-(Paths.length?2:0)); // OLE
		Paths.push(name);
		var o = { name: name };
		o.type = EntryTypes[read(1)];
		o.color = read(1);
		o.left = read(4); if(o.left === NOSTREAM) delete o.left;
		o.right = read(4); if(o.right === NOSTREAM) delete o.right;
		o.child = read(4); if(o.child === NOSTREAM) delete o.child;
		o.clsid = read(16);
		o.state = read(4);
		var ctime = read(8); if(ctime != "0000000000000000") o.ctime = ctime;
		var mtime = read(8); if(mtime != "0000000000000000") o.mtime = mtime;
		o.start = read(4);
		o.size = read(4);
		if(o.type === 'root') { //root entry
			minifat_store = o.start;
			if(nmfs > 0 && minifat_store !== ENDOFCHAIN) sector_list[minifat_store].name = "!StreamData";
			minifat_size = o.size;
		} else if(o.size >= ms_cutoff_size) {
			o.storage = 'fat';
			if(!sector_list[o.start] && dir_start > 0) o.start = (o.start + dir_start) % sectors.length;
			sector_list[o.start].name = o.name;
			o.content = sector_list[o.start].data.slice(0,o.size);
			prep_blob(o.content);
		} else {
			o.storage = 'minifat';
			w = o.start * mssz;
			if(minifat_store !== ENDOFCHAIN && o.start !== ENDOFCHAIN) {
				o.content = sector_list[minifat_store].data.slice(w,w+o.size);
				prep_blob(o.content);
			}
		}
		if(o.ctime) {
			var ct = blob.slice(blob.l-24, blob.l-16);
			var c2 = (ct.readUInt32LE(4)/1e7)*Math.pow(2,32)+ct.readUInt32LE(0)/1e7;
			o.ct = new Date((c2 - 11644473600)*1000);
		}
		if(o.mtime) {
			var mt = blob.slice(blob.l-16, blob.l-8);
			var m2 = (mt.readUInt32LE(4)/1e7)*Math.pow(2,32)+mt.readUInt32LE(0)/1e7;
			o.mt = new Date((m2 - 11644473600)*1000);
		}
		files[name] = o;
		FileIndex.push(o);
	}
}
read_directory(dir_start);

/* [MS-CFB] 2.6.4 Red-Black Tree */
function build_full_paths(Dir, pathobj, paths, patharr) {
	var i;
	var dad = new Array(patharr.length);

	var q = new Array(patharr.length);

	for(i=0; i != dad.length; ++i) { dad[i]=q[i]=i; paths[i]=patharr[i]; }

	for(i = q[0]; typeof i !== "undefined"; i = q.shift()) {
		if(Dir[i].child) dad[Dir[i].child] = i;
		if(Dir[i].left) { dad[Dir[i].left] = dad[i]; q.push(Dir[i].left); }
		if(Dir[i].right) { dad[Dir[i].right] = dad[i]; q.push(Dir[i].right); }
	}

	for(i=1; i !== paths.length; ++i) {
		if(Dir[i].type === "unknown") continue;
		var j = dad[i];
		if(j === 0) paths[i] = paths[0] + "/" + paths[i];
		else while(j !== 0) {
			paths[i] = paths[j] + "/" + paths[i];
			j = dad[j];
		}
		dad[i] = 0;
	}

	paths[0] += "/";
	for(i=1; i !== paths.length; ++i) if(Dir[i].type !== 'stream') paths[i] += "/";
	for(i=0; i !== paths.length; ++i) pathobj[paths[i]] = FileIndex[i];
}
build_full_paths(FileIndex, FullPathDir, FullPaths, Paths);

var root_name = Paths.shift();
Paths.root = root_name;

/* [MS-CFB] 2.6.4 (Unicode 3.0.1 case conversion) */
function find_path(path) {
	if(path[0] === "/") path = root_name + path;
	var UCNames = (path.indexOf("/") !== -1 ? FullPaths : Paths).map(function(x) { return x.toUpperCase(); });
	var UCPath = path.toUpperCase();
	var w = UCNames.indexOf(UCPath);
	if(w === -1) return null;
	return path.indexOf("/") !== -1 ? FileIndex[w] : files[Paths[w]];
}

var rval = {
	raw: {header: header, sectors: sectors},
	FileIndex: FileIndex,
	FullPaths: FullPaths,
	FullPathDir: FullPathDir,
	find: find_path
};

//for(var name in files) {
//	switch(name) {
//		/* [MS-OSHARED] 2.3.3.2.2 Document Summary Information Property Set */
//		case '!DocumentSummaryInformation':
//			rval.DocSummary = parse_PropertySetStream(files[name], DocSummaryPIDDSI); break;
//		/* [MS-OSHARED] 2.3.3.2.1 Summary Information Property Set*/
//		case '!SummaryInformation':
//			rval.Summary = parse_PropertySetStream(files[name], SummaryPIDSI); break;
//	}
//}

return rval;
} // parse


function readFileSync(filename) {
	var fs = require('fs');
	var file = fs.readFileSync(filename);
	return parse(file);
}

function readSync(blob, options) {
	var o = options || {};
	switch((o.type || "base64")) {
		case "file": return readFileSync(blob);
		case "base64": blob = Base64.decode(blob);
		/* falls through */
		case "binary": blob = s2a(blob); break;
	}
	return parse(blob);
}

exports.read = readSync;
exports.parse = parse;
return exports;
})();

/** CFB Constants */
{
	/* 2.1 Compund File Sector Numbers and Types */
	var MAXREGSECT = 0xFFFFFFFA;
	var DIFSECT = 0xFFFFFFFC;
	var FATSECT = 0xFFFFFFFD;
	var ENDOFCHAIN = 0xFFFFFFFE;
	var FREESECT = 0xFFFFFFFF;
	/* 2.2 Compound File Header */
	var HEADER_SIGNATURE = 'd0cf11e0a1b11ae1';
	var HEADER_MINOR_VERSION = '3e00';
	var MAXREGSID = 0xFFFFFFFA;
	var NOSTREAM = 0xFFFFFFFF;
	var HEADER_CLSID = '00000000000000000000000000000000';
	/* 2.6.1 Compound File Directory Entry */
	var EntryTypes = ['unknown','storage','stream','lockbytes','property','root'];
}

if(typeof require !== 'undefined' && typeof exports !== 'undefined') {
	Buffers = Array;
	Buffers.prototype.toBuffer = function() {
		return Buffer.concat(this[0]);
	};
	var fs = require('fs');
	//exports.read = CFB.read;
	//exports.parse = CFB.parse;
	//exports.ReadShift = ReadShift;
	//exports.prep_blob = prep_blob;
	exports.main = function(args) {
		var cfb = CFB.read(args[0], {type:'file'});
		console.log(cfb);
	};
	if(typeof module !== 'undefined' && require.main === module)
		exports.main(process.argv.slice(2));
} else {
	Buffers = Array;
	Buffers.prototype.toBuffer = function() {
		var x = [];
		for(var i = 0; i != this[0].length; ++i) { x = x.concat(this[0][i]); }
		return x;
	};
}

/* sections refer to MS-XLS unless otherwise stated */

/* --- Simple Utilities --- */
function parsenoop(blob, length) { blob.read_shift(length); return; }
function parsenoop2(blob, length) { blob.read_shift(length); return null; }

function parslurp(blob, length, cb) {
	var arr = [], target = blob.l + length;
	while(blob.l < target) arr.push(cb(blob, target - blob.l));
	if(target !== blob.l) throw "Slurp error";
	return arr;
}

function parslurp2(blob, length, cb) {
	var arr = [], target = blob.l + length, len = blob.read_shift(2);
	while(len-- !== 0) arr.push(cb(blob, target - blob.l));
	if(target !== blob.l) throw "Slurp error";
	return arr;
}

function parsebool(blob, length) { return blob.read_shift(length) === 0x1; }

function parseuint16(blob, length) { return blob.read_shift(2, 'u'); }
function parseuint16a(blob, length) { return parslurp(blob,length,parseuint16);}

/* --- 2.5 Structures --- */

/* [MS-XLS] 2.5.14 Boolean */
var parse_Boolean = parsebool;

/* [MS-XLS] 2.5.10 Bes (boolean or error) */
function parse_Bes(blob) {
	var v = blob.read_shift(1), t = blob.read_shift(1);
	return t === 0x01 ? BERR[v] : v === 0x01;
}

/* [MS-XLS] 2.5.240 ShortXLUnicodeString */
function parse_ShortXLUnicodeString(blob) {
	var read = blob.read_shift.bind(blob);
	var cch = read(1);
	var fHighByte = read(1);
	var retval;
	var width = 1 + (fHighByte === 0 ? 0 : 1), encoding = fHighByte ? 'dbcs' : 'sbcs';
	retval = cch ? read(encoding, cch) : "";
	return retval;
}

/* 2.5.293 XLUnicodeRichExtendedString */
function parse_XLUnicodeRichExtendedString(blob) {
	var read_shift = blob.read_shift.bind(blob);
	var cch = read_shift(2), flags = read_shift(1);
	var fHighByte = flags & 0x1, fExtSt = flags & 0x4, fRichSt = flags & 0x8;
	var width = 1 + (flags & 0x1); // 0x0 -> utf8, 0x1 -> dbcs
	var cRun, cbExtRst;
	if(fRichSt) cRun = read_shift(2);
	if(fExtSt) cbExtRst = read_shift(4);
	var encoding = (flags & 0x1) ? 'dbcs' : 'sbcs';
	var msg = cch === 0 ? "" : read_shift(encoding, cch);
	if(fRichSt) blob.l += 4 * cRun; //TODO: parse this
	if(fExtSt) blob.l += cbExtRst; //TODO: parse this
	return msg;
}

/* 2.5.296 XLUnicodeStringNoCch */
function parse_XLUnicodeStringNoCch(blob, cch) {
	var read = blob.read_shift.bind(blob);
	var fHighByte = read(1);
	var retval;
	if(fHighByte===0) { retval = blob.utf8(blob.l, blob.l+cch); blob.l += cch; }
	else { retval = blob.read_shift('dbcs', cch); }
	return retval;
}

/* 2.5.294 XLUnicodeString */
function parse_XLUnicodeString(blob) {
	var cch = blob.read_shift(2);
	if(cch === 0) { blob.l++; return ""; }
	return parse_XLUnicodeStringNoCch(blob, cch);
}

/* 2.5.342 Xnum */
function parse_Xnum(blob, length) { return blob.read_shift('ieee754'); }



/* 2.5.19 */
function parse_Cell(blob, length) {
	var rw = blob.read_shift(2); // 0-indexed
	var col = blob.read_shift(2);
	var ixfe = blob.read_shift(2);
	return {r:rw, c:col, ixfe:ixfe};
}

/* 2.5.134 */
function parse_frtHeader(blob) {
	var read = blob.read_shift.bind(blob);
	var rt = read(2);
	var flags = read(2); // TODO: parse these flags
	read(8);
	return {type: rt, flags: flags};
}



function parse_OptXLUnicodeString(blob, length) { return length === 0 ? "" : parse_XLUnicodeString(blob); }

/* 2.5.158 */
var HIDEOBJENUM = ['SHOWALL', 'SHOWPLACEHOLDER', 'HIDEALL'];
var parse_HideObjEnum = parseuint16;

/* 2.5.344 */
function parse_XTI(blob, length) {
	var read = blob.read_shift.bind(blob);
	var iSupBook = read(2), itabFirst = read(2,'i'), itabLast = read(2,'i');
	return [iSupBook, itabFirst, itabLast];
}

/* 2.5.217 */
function parse_RkNumber(blob) {
	var b = blob.slice(blob.l, blob.l+4);
	var fX100 = b[0] & 1, fInt = b[0] & 2;
	blob.l+=4;
	b[0] &= ~3;
	var RK = fInt === 0 ? [0,0,0,0,b[0],b[1],b[2],b[3]].readDoubleLE(0) : b.readInt32LE(0)>>2;
	return fX100 ? RK/100 : RK;
}

/* 2.5.218 */
function parse_RkRec(blob, length) {
	var ixfe = blob.read_shift(2);
	var RK = parse_RkNumber(blob);
	//console.log("::", ixfe, RK,";;");
	return [ixfe, RK];
}

/* 2.5.1 */
function parse_AddinUdf(blob, length) {
	blob.l += 4; length -= 4;
	var l = blob.l + length;
	var udfName = parse_ShortXLUnicodeString(blob, length);
	var cb = blob.read_shift(2);
	l -= blob.l;
	if(cb !== l) throw "Malformed AddinUdf: padding = " + l + " != " + cb;
	blob.l += cb;
	return udfName;
}

/* 2.5.209 TODO: Check sizes */
function parse_Ref8U(blob, length) {
	var rwFirst = blob.read_shift(2);
	var rwLast = blob.read_shift(2);
	var colFirst = blob.read_shift(2);
	var colLast = blob.read_shift(2);
	return {s:{c:colFirst, r:rwFirst}, e:{c:colLast,r:rwLast}};
}

/* 2.5.211 */
function parse_RefU(blob, length) {
	var rwFirst = blob.read_shift(2);
	var rwLast = blob.read_shift(2);
	var colFirst = blob.read_shift(1);
	var colLast = blob.read_shift(1);
	return {s:{c:colFirst, r:rwFirst}, e:{c:colLast,r:rwLast}};
}

/* 2.5.207 */
var parse_Ref = parse_RefU;

/* --- 2.4 Records --- */

/* 2.4.21 */
function parse_BOF(blob, length) {
	var o = {};
	o.BIFFVer = blob.read_shift(2); length -= 2;
	if(o.BIFFVer != 0x0600) throw "Unexpected BIFF Ver " + o.BIFFVer;
	blob.read_shift(length);
	return o;
}


/* 2.4.146 */
function parse_InterfaceHdr(blob, length) {
	var q;
	if((q=blob.read_shift(2))!==0x04b0) throw 'InterfaceHdr codePage ' + q;
	return 0x04b0;
}


/* 2.4.349 */
function parse_WriteAccess(blob, length, opts) {
	if(opts.enc) { blob.l += length; return ""; }
	var l = blob.l;
	// TODO: make sure XLUnicodeString doesnt overrun
	var UserName = parse_XLUnicodeString(blob);
	blob.read_shift(length + l - blob.l);
	return UserName;
}

/* 2.4.28 */
function parse_BoundSheet8(blob, length) {
	var read = blob.read_shift.bind(blob);
	var pos = read(4);
	var hidden = read(1) >> 6;
	var dt = read(1);
	switch(dt) {
		case 0: dt = 'Worksheet'; break;
		case 1: dt = 'Macrosheet'; break;
		case 2: dt = 'Chartsheet'; break;
		case 6: dt = 'VBAModule'; break;
	}
	var name = parse_ShortXLUnicodeString(blob);
	return { pos:pos, hs:hidden, dt:dt, name:name };
}

/* 2.4.265 TODO */
function parse_SST(blob, length) {
	var read = blob.read_shift.bind(blob);
	var cnt = read(4);
	var ucnt = read(4);
	var strs = [];
	for(var i = 0; i != ucnt; ++i) {
		strs.push(parse_XLUnicodeRichExtendedString(blob));
	}
	strs.Count = cnt; strs.Unique = ucnt;
	return strs;
}

/* 2.4.107 */
function parse_ExtSST(blob, length) {
	var read = blob.read_shift.bind(blob);
	var extsst = {};
	extsst.dsst = read(2);
	blob.read_shift(length-2);
	return extsst;
}


/* 2.4.221 TODO*/
function parse_Row(blob, length) {
	var read = blob.read_shift.bind(blob);
	var rw = read(2), col = read(2), Col = read(2), rht = read(2);
	read(4); // reserved(2), unused(2)
	var flags = read(1); // various flags
	read(1); // reserved
	read(2); //ixfe, other flags
	return {r:rw, c:col, cnt:Col-col};
}


/* 2.4.125 */
function parse_ForceFullCalculation(blob, length) {
	var header = parse_frtHeader(blob);
	if(header.type != 0x08A3) throw "Invalid Future Record " + header.type;
	var fullcalc = blob.read_shift(4);
	return fullcalc !== 0x0;
}


var parse_CompressPictures = parsenoop2; /* 2.4.55 Not interesting */



/* 2.4.215 rt */
function parse_RecalcId(blob, length) {
	blob.read_shift(2);
	return blob.read_shift(4);
}

/* 2.4.87 */
function parse_DefaultRowHeight (blob, length) {
	var f = blob.read_shift(2), miyRw;
	miyRw = blob.read_shift(2); // flags & 0x02 -> hidden, else empty
	var fl = {Unsynced:f&1,DyZero:(f&2)>>1,ExAsc:(f&4)>>2,ExDsc:(f&8)>>3};
	return [fl, miyRw];
}

/* 2.4.345 TODO */
function parse_Window1(blob, length) {
	var read = blob.read_shift.bind(blob);
	var xWn = read(2), yWn = read(2), dxWn = read(2), dyWn = read(2);
	var flags = read(2), iTabCur = read(2), iTabFirst = read(2);
	var ctabSel = read(2), wTabRatio = read(2);
	return { Pos: [xWn, yWn], Dim: [dxWn, dyWn], Flags: flags, CurTab: iTabCur,
		FirstTab: iTabFirst, Selected: ctabSel, TabRatio: wTabRatio };
}

/* 2.4.122 TODO */
function parse_Font(blob, length) {
	blob.l += 14;
	var name = parse_ShortXLUnicodeString(blob);
	return name;
}

/* 2.4.149 */
function parse_LabelSst(blob, length) {
	var cell = parse_Cell(blob);
	cell.isst = blob.read_shift(4);
	return cell;
}

/* 2.4.126 Number Formats */
function parse_Format(blob, length) {
	var ifmt = blob.read_shift(2);
	var fmtstr = parse_XLUnicodeString(blob);
	return [ifmt, fmtstr];
}

/* 2.4.90 */
function parse_Dimensions(blob, length) {
	var read = blob.read_shift.bind(blob);
	var r = read(4), R = read(4), c = read(2), C = read(2);
	read(2);
	return {s: {r:r, c:c}, e: {r:R, c:C}};
}

/* 2.4.220 */
function parse_RK(blob, length) {
	var rw = blob.read_shift(2), col = blob.read_shift(2);
	var rkrec = parse_RkRec(blob);
	return {r:rw, c:col, ixfe:rkrec[0], rknum:rkrec[1]};
}

/* 2.4.175 */
function parse_MulRk(blob, length) {
	var target = blob.l + length - 2;
	var rw = blob.read_shift(2), col = blob.read_shift(2);
	var rkrecs = [];
	while(blob.l < target) rkrecs.push(parse_RkRec(blob));
	if(blob.l !== target) throw "MulRK read error";
	var lastcol = blob.read_shift(2);
	if(rkrecs.length != lastcol - col + 1) throw "MulRK length mismatch";
	return {r:rw, c:col, C:lastcol, rkrec:rkrecs};
}

/* 2.4.353 */
var parse_XF = parsenoop;

/* 2.4.134 */
function parse_Guts(blob, length) {
	blob.l += 4;
	var out = [blob.read_shift(2), blob.read_shift(2)];
	if(out[0] !== 0) out[0]--;
	if(out[1] !== 0) out[1]--;
	if(out[0] > 7 || out[1] > 7) throw "Bad Gutters: " + out;
	return out;
}

/* 2.4.24 */
function parse_BoolErr(blob, length) {
	var cell = parse_Cell(blob, 6);
	var val = parse_Bes(blob, 2);
	cell.val = val;
	cell.t = (val === true || val === false) ? 'b' : 'e';
	return cell;
}

/* 2.4.180 Number */
function parse_Number(blob, length) {
	var cell = parse_Cell(blob, 6);
	var xnum = parse_Xnum(blob, 8);
	cell.val = xnum;
	return cell;
}

var parse_XLHeaderFooter = parse_OptXLUnicodeString; // TODO: parse 2.4.136

/* 2.4.271 */
function parse_SupBook(blob, length, opts) {
	var end = blob.l + length;
	var ctab = blob.read_shift(2);
	var cch = blob.read_shift(2);
	var virtPath;
	if(cch >=0x01 && cch <=0xff) virtPath = parse_XLUnicodeStringNoCch(blob, cch);
	var rgst = blob.read_shift(end - blob.l);
	opts.sbcch = cch;
	return [cch, ctab, virtPath, rgst];
}

/* 2.4.105 TODO */
function parse_ExternName(blob, length, opts) {
	var flags = blob.read_shift(2);
	var body;
	var o = {
		fBuiltIn: flags & 0x01,
		fWantAdvise: (flags >>> 1) & 0x01,
		fWantPict: (flags >>> 2) & 0x01,
		fOle: (flags >>> 3) & 0x01,
		fOleLink: (flags >>> 4) & 0x01,
		cf: (flags >>> 5) & 0x3FF,
		fIcon: flags >>> 15 & 0x01
	};
	if(opts.sbcch === 0x3A01) body = parse_AddinUdf(blob, length-2);
	//else throw new Error("unsupported SupBook cch: " + opts.sbcch);
	o.body = blob.read_shift(length-2);
	return o;
}

/* 2.4.150 TODO */
function parse_Lbl(blob, length, opts) {
	var target = blob.l + length;
	var flags = blob.read_shift(2);
	var chKey = blob.read_shift(1);
	var cch = blob.read_shift(1);
	var cce = blob.read_shift(2);
	blob.l += 2;
	var itab = blob.read_shift(2);
	blob.l += 4;
	var name = parse_XLUnicodeStringNoCch(blob, cch);
	var rgce = parse_NameParsedFormula(blob, target - blob.l, cce);
	return {
		chKey: chKey,
		Name: name,
		rgce: rgce
	};
}

/* 2.4.106 TODO: verify supbook manipulation */
function parse_ExternSheet(blob, length, opts) {
	var o = parslurp2(blob,length,parse_XTI);
	var oo = [];
	if(opts.sbcch === 0x0401) {
		for(var i = 0; i != o.length; ++i) oo.push(opts.snames[o[i][1]]);
		return oo;
	}
	else return o;
}

/* 2.4.260 */
function parse_ShrFmla(blob, length, opts) {
	var ref = parse_RefU(blob, 6);
	blob.l++;
	var cUse = blob.read_shift(1);
	length -= 8;
	return [parse_SharedParsedFormula(blob, length, opts), cUse];
}

/* 2.4.4 TODO */
function parse_Array(blob, length, opts) {
	var ref = parse_Ref(blob, 6);
	blob.l += 6; length -= 12; /* TODO: fAlwaysCalc */
	return [ref, parse_ArrayParsedFormula(blob, length, opts, ref)];
}

/* 2.4.173 */
function parse_MTRSettings(blob, length) {
	var fMTREnabled = blob.read_shift(4) !== 0x00;
	var fUserSetThreadCount = blob.read_shift(4) !== 0x00;
	var cUserThreadCount = blob.read_shift(4);
	return [fMTREnabled, fUserSetThreadCount, cUserThreadCount];
}

var parse_Backup = parsebool; /* 2.4.14 */
var parse_Blank = parse_Cell; /* 2.4.20 Just the cell */
var parse_BottomMargin = parse_Xnum; /* 2.4.27 */
var parse_BuiltInFnGroupCount = parseuint16; /* 2.4.30 0x0E or 0x10 but excel 2011 generates 0x11? */
var parse_CalcCount = parseuint16; /* 2.4.31 #Iterations */
var parse_CalcDelta = parse_Xnum; /* 2.4.32 */
var parse_CalcIter = parsebool;  /* 2.4.33 1=iterative calc */
var parse_CalcMode = parseuint16; /* 2.4.34 0=manual, 1=auto (def), 2=table */
var parse_CalcPrecision = parsebool; /* 2.4.35 */
var parse_CalcRefMode = parsenoop2; /* 2.4.36 */
var parse_CalcSaveRecalc = parsebool; /* 2.4.37 */
var parse_CodePage = parseuint16; /* 2.4.52 */
var parse_Compat12 = parsebool; /* 2.4.54 true = no compatibility check */
var parse_Country = parseuint16a; /* 2.4.63 -- two ints, 1 to 981 */
var parse_Date1904 = parsebool; /* 2.4.77 - 1=1904,0=1900 */
var parse_DefColWidth = parseuint16; /* 2.4.89 */
var parse_DSF = parsenoop2; /* 2.4.94 -- MUST be ignored */
var parse_EntExU2 = parsenoop2; /* 2.4.102 -- Explicitly says to ignore */
var parse_EOF = parsenoop2; /* 2.4.103 */
var parse_Excel9File = parsenoop2; /* 2.4.104 -- Optional and unused */
var parse_FeatHdr = parsenoop2; /* 2.4.112 */
var parse_FontX = parseuint16; /* 2.4.123 */
var parse_Footer = parse_XLHeaderFooter; /* 2.4.124 */
var parse_GridSet = parseuint16; /* 2.4.132, =1 */
var parse_HCenter = parsebool; /* 2.4.135 sheet centered horizontal on print */
var parse_Header = parse_XLHeaderFooter; /* 2.4.136 */
var parse_HideObj = parse_HideObjEnum; /* 2.4.139 */
var parse_InterfaceEnd = parsenoop2; /* 2.4.145 -- noop */
var parse_LeftMargin = parse_Xnum; /* 2.4.151 */
var parse_Mms = parsenoop2; /* 2.4.169 -- Explicitly says to ignore */
var parse_ObjProtect = parsebool; /* 2.4.183 -- must be 1 if present */
var parse_Password = parseuint16; /* 2.4.191 */
var parse_PrintGrid = parsebool; /* 2.4.202 */
var parse_PrintRowCol = parsebool; /* 2.4.203 */
var parse_PrintSize = parseuint16; /* 2.4.204 0:3 */
var parse_Prot4Rev = parsebool; /* 2.4.205 */
var parse_Prot4RevPass = parseuint16; /* 2.4.206 */
var parse_Protect = parsebool; /* 2.4.207 */
var parse_RefreshAll = parsebool; /* 2.4.217 -- must be 0 if not template */
var parse_RightMargin = parse_Xnum; /* 2.4.219 */
var parse_RRTabId = parseuint16a; /* 2.4.241 */
var parse_ScenarioProtect = parsebool; /* 2.4.245 */
var parse_Scl = parseuint16a; /* 2.4.247 num, den */
var parse_String = parse_XLUnicodeString; /* 2.4.268 */
var parse_SxBool = parsebool; /* 2.4.274 */
var parse_TopMargin = parse_Xnum; /* 2.4.328 */
var parse_UsesELFs = parsebool; /* 2.4.337 -- should be 0 */
var parse_VCenter = parsebool; /* 2.4.342 */
var parse_WinProtect = parsebool; /* 2.4.347 */
var parse_WriteProtect = parsenoop; /* 2.4.350 empty record */


/* ---- */
var parse_VerticalPageBreaks = parsenoop;
var parse_HorizontalPageBreaks = parsenoop;
var parse_Note = parsenoop;
var parse_Selection = parsenoop;
var parse_Continue = parsenoop;
var parse_Pane = parsenoop;
var parse_Pls = parsenoop;
var parse_DCon = parsenoop;
var parse_DConRef = parsenoop;
var parse_DConName = parsenoop;
var parse_XCT = parsenoop;
var parse_CRN = parsenoop;
var parse_FileSharing = parsenoop;
var parse_Obj = parsenoop;
var parse_Uncalced = parsenoop;
var parse_Template = parsenoop;
var parse_Intl = parsenoop;
var parse_ColInfo = parsenoop;
var parse_WsBool = parsenoop;
var parse_Sort = parsenoop;
var parse_Palette = parsenoop;
var parse_Sync = parsenoop;
var parse_LPr = parsenoop;
var parse_DxGCol = parsenoop;
var parse_FnGroupName = parsenoop;
var parse_FilterMode = parsenoop;
var parse_AutoFilterInfo = parsenoop;
var parse_AutoFilter = parsenoop;
var parse_Setup = parsenoop;
var parse_ScenMan = parsenoop;
var parse_SCENARIO = parsenoop;
var parse_SxView = parsenoop;
var parse_Sxvd = parsenoop;
var parse_SXVI = parsenoop;
var parse_SxIvd = parsenoop;
var parse_SXLI = parsenoop;
var parse_SXPI = parsenoop;
var parse_DocRoute = parsenoop;
var parse_RecipName = parsenoop;
var parse_MulBlank = parsenoop;
var parse_SXDI = parsenoop;
var parse_SXDB = parsenoop;
var parse_SXFDB = parsenoop;
var parse_SXDBB = parsenoop;
var parse_SXNum = parsenoop;
var parse_SxErr = parsenoop;
var parse_SXInt = parsenoop;
var parse_SXString = parsenoop;
var parse_SXDtr = parsenoop;
var parse_SxNil = parsenoop;
var parse_SXTbl = parsenoop;
var parse_SXTBRGIITM = parsenoop;
var parse_SxTbpg = parsenoop;
var parse_ObProj = parsenoop;
var parse_SXStreamID = parsenoop;
var parse_DBCell = parsenoop;
var parse_SXRng = parsenoop;
var parse_SxIsxoper = parsenoop;
var parse_BookBool = parsenoop;
var parse_DbOrParamQry = parsenoop;
var parse_OleObjectSize = parsenoop;
var parse_SXVS = parsenoop;
var parse_MergeCells = parsenoop;
var parse_BkHim = parsenoop;
var parse_MsoDrawingGroup = parsenoop;
var parse_MsoDrawing = parsenoop;
var parse_MsoDrawingSelection = parsenoop;
var parse_PhoneticInfo = parsenoop;
var parse_SxRule = parsenoop;
var parse_SXEx = parsenoop;
var parse_SxFilt = parsenoop;
var parse_SxDXF = parsenoop;
var parse_SxItm = parsenoop;
var parse_SxName = parsenoop;
var parse_SxSelect = parsenoop;
var parse_SXPair = parsenoop;
var parse_SxFmla = parsenoop;
var parse_SxFormat = parsenoop;
var parse_SXVDEx = parsenoop;
var parse_SXFormula = parsenoop;
var parse_SXDBEx = parsenoop;
var parse_RRDInsDel = parsenoop;
var parse_RRDHead = parsenoop;
var parse_RRDChgCell = parsenoop;
var parse_RRDRenSheet = parsenoop;
var parse_RRSort = parsenoop;
var parse_RRDMove = parsenoop;
var parse_RRFormat = parsenoop;
var parse_RRAutoFmt = parsenoop;
var parse_RRInsertSh = parsenoop;
var parse_RRDMoveBegin = parsenoop;
var parse_RRDMoveEnd = parsenoop;
var parse_RRDInsDelBegin = parsenoop;
var parse_RRDInsDelEnd = parsenoop;
var parse_RRDConflict = parsenoop;
var parse_RRDDefName = parsenoop;
var parse_RRDRstEtxp = parsenoop;
var parse_LRng = parsenoop;
var parse_CUsr = parsenoop;
var parse_CbUsr = parsenoop;
var parse_UsrInfo = parsenoop;
var parse_UsrExcl = parsenoop;
var parse_FileLock = parsenoop;
var parse_RRDInfo = parsenoop;
var parse_BCUsrs = parsenoop;
var parse_UsrChk = parsenoop;
var parse_UserBView = parsenoop;
var parse_UserSViewBegin = parsenoop; // overloaded
var parse_UserSViewEnd = parsenoop;
var parse_RRDUserView = parsenoop;
var parse_Qsi = parsenoop;
var parse_CondFmt = parsenoop;
var parse_CF = parsenoop;
var parse_DVal = parsenoop;
var parse_DConBin = parsenoop;
var parse_TxO = parsenoop;
var parse_HLink = parsenoop;
var parse_Lel = parsenoop;
var parse_CodeName = parse_XLUnicodeString;
var parse_SXFDBType = parsenoop;
var parse_ObNoMacros = parsenoop;
var parse_Dv = parsenoop;
var parse_Label = parsenoop;
var parse_Index = parsenoop;
var parse_Table = parsenoop;
var parse_Window2 = parsenoop;
var parse_Style = parsenoop;
var parse_BigName = parsenoop;
var parse_ContinueBigName = parsenoop;
var parse_HLinkTooltip = parsenoop;
var parse_WebPub = parsenoop;
var parse_QsiSXTag = parsenoop;
var parse_DBQueryExt = parsenoop;
var parse_ExtString = parsenoop;
var parse_TxtQry = parsenoop;
var parse_Qsir = parsenoop;
var parse_Qsif = parsenoop;
var parse_RRDTQSIF = parsenoop;
var parse_OleDbConn = parsenoop;
var parse_WOpt = parsenoop;
var parse_SXViewEx = parsenoop;
var parse_SXTH = parsenoop;
var parse_SXPIEx = parsenoop;
var parse_SXVDTEx = parsenoop;
var parse_SXViewEx9 = parsenoop;
var parse_ContinueFrt = parsenoop;
var parse_RealTimeData = parsenoop;
var parse_ChartFrtInfo = parsenoop;
var parse_FrtWrapper = parsenoop;
var parse_StartBlock = parsenoop;
var parse_EndBlock = parsenoop;
var parse_StartObject = parsenoop;
var parse_EndObject = parsenoop;
var parse_CatLab = parsenoop;
var parse_YMult = parsenoop;
var parse_SXViewLink = parsenoop;
var parse_PivotChartBits = parsenoop;
var parse_FrtFontList = parsenoop;
var parse_SheetExt = parsenoop;
var parse_BookExt = parsenoop;
var parse_SXAddl = parsenoop;
var parse_CrErr = parsenoop;
var parse_HFPicture = parsenoop;
var parse_Feat = parsenoop;
var parse_DataLabExt = parsenoop;
var parse_DataLabExtContents = parsenoop;
var parse_CellWatch = parsenoop;
var parse_FeatHdr11 = parsenoop;
var parse_Feature11 = parsenoop;
var parse_DropDownObjIds = parsenoop;
var parse_ContinueFrt11 = parsenoop;
var parse_DConn = parsenoop;
var parse_List12 = parsenoop;
var parse_Feature12 = parsenoop;
var parse_CondFmt12 = parsenoop;
var parse_CF12 = parsenoop;
var parse_CFEx = parsenoop;
var parse_XFCRC = parsenoop;
var parse_XFExt = parsenoop;
var parse_AutoFilter12 = parsenoop;
var parse_ContinueFrt12 = parsenoop;
var parse_MDTInfo = parsenoop;
var parse_MDXStr = parsenoop;
var parse_MDXTuple = parsenoop;
var parse_MDXSet = parsenoop;
var parse_MDXProp = parsenoop;
var parse_MDXKPI = parsenoop;
var parse_MDB = parsenoop;
var parse_PLV = parsenoop;
var parse_DXF = parsenoop;
var parse_TableStyles = parsenoop;
var parse_TableStyle = parsenoop;
var parse_TableStyleElement = parsenoop;
var parse_StyleExt = parsenoop;
var parse_NamePublish = parsenoop;
var parse_NameCmt = parsenoop;
var parse_SortData = parsenoop;
var parse_Theme = parsenoop;
var parse_GUIDTypeLib = parsenoop;
var parse_FnGrp12 = parsenoop;
var parse_NameFnGrp12 = parsenoop;
var parse_HeaderFooter = parsenoop;
var parse_CrtLayout12 = parsenoop;
var parse_CrtMlFrt = parsenoop;
var parse_CrtMlFrtContinue = parsenoop;
var parse_ShapePropsStream = parsenoop;
var parse_TextPropsStream = parsenoop;
var parse_RichTextStream = parsenoop;
var parse_CrtLayout12A = parsenoop;
var parse_Units = parsenoop;
var parse_Chart = parsenoop;
var parse_Series = parsenoop;
var parse_DataFormat = parsenoop;
var parse_LineFormat = parsenoop;
var parse_MarkerFormat = parsenoop;
var parse_AreaFormat = parsenoop;
var parse_PieFormat = parsenoop;
var parse_AttachedLabel = parsenoop;
var parse_SeriesText = parsenoop;
var parse_ChartFormat = parsenoop;
var parse_Legend = parsenoop;
var parse_SeriesList = parsenoop;
var parse_Bar = parsenoop;
var parse_Line = parsenoop;
var parse_Pie = parsenoop;
var parse_Area = parsenoop;
var parse_Scatter = parsenoop;
var parse_CrtLine = parsenoop;
var parse_Axis = parsenoop;
var parse_Tick = parsenoop;
var parse_ValueRange = parsenoop;
var parse_CatSerRange = parsenoop;
var parse_AxisLine = parsenoop;
var parse_CrtLink = parsenoop;
var parse_DefaultText = parsenoop;
var parse_Text = parsenoop;
var parse_ObjectLink = parsenoop;
var parse_Frame = parsenoop;
var parse_Begin = parsenoop;
var parse_End = parsenoop;
var parse_PlotArea = parsenoop;
var parse_Chart3d = parsenoop;
var parse_PicF = parsenoop;
var parse_DropBar = parsenoop;
var parse_Radar = parsenoop;
var parse_Surf = parsenoop;
var parse_RadarArea = parsenoop;
var parse_AxisParent = parsenoop;
var parse_LegendException = parsenoop;
var parse_ShtProps = parsenoop;
var parse_SerToCrt = parsenoop;
var parse_AxesUsed = parsenoop;
var parse_SBaseRef = parsenoop;
var parse_SerParent = parsenoop;
var parse_SerAuxTrend = parsenoop;
var parse_IFmtRecord = parsenoop;
var parse_Pos = parsenoop;
var parse_AlRuns = parsenoop;
var parse_BRAI = parsenoop;
var parse_SerAuxErrBar = parsenoop;
var parse_ClrtClient = parsenoop;
var parse_SerFmt = parsenoop;
var parse_Chart3DBarShape = parsenoop;
var parse_Fbi = parsenoop;
var parse_BopPop = parsenoop;
var parse_AxcExt = parsenoop;
var parse_Dat = parsenoop;
var parse_PlotGrowth = parsenoop;
var parse_SIIndex = parsenoop;
var parse_GelFrame = parsenoop;
var parse_BopPopCustom = parsenoop;
var parse_Fbi2 = parsenoop;


/* [MS-OFFCRYPTO] 2.1.4 Version */
function parse_Version(blob, length) {
	var o = {};
	o.Major = blob.read_shift(2);
	o.Minor = blob.read_shift(2);
	return o;
}
/* [MS-OFFCRYPTO] 2.3.2 Encryption Header */
function parse_EncryptionHeader(blob, length) {
	var read = blob.read_shift.bind(blob);
	var o = {};
	o.Flags = read(4);

	// Check if SizeExtra is 0x00000000
	var tmp = read(4);
	if(tmp !== 0) throw 'Unrecognized SizeExtra: ' + tmp;

	o.AlgID = read(4);
	switch(o.AlgID) {
		case 0: case 0x6801: case 0x660E: case 0x660F: case 0x6610: break;
		default: throw 'Unrecognized encryption algorithm: ' + o.AlgID;
	}
	parsenoop(blob, length-12);
	return o;
}

/* [MS-OFFCRYPTO] 2.3.3 Encryption Verifier */
function parse_EncryptionVerifier(blob, length) {
	return parsenoop(blob, length);
}
/* [MS-OFFCRYPTO] 2.3.5.1 RC4 CryptoAPI Encryption Header */
function parse_RC4CryptoHeader(blob, length) {
	var o = {};
	var vers = o.EncryptionVersionInfo = parse_Version(blob, 4); length -= 4;
	if(vers.Minor != 2) throw 'unrecognized minor version code: ' + vers.Minor;
	if(vers.Major > 4 || vers.Major < 2) throw 'unrecognized major version code: ' + vers.Major;
	o.Flags = blob.read_shift(4); length -= 4;
	var sz = blob.read_shift(4); length -= 4;
	o.EncryptionHeader = parse_EncryptionHeader(blob, sz); length -= sz;
	o.EncryptionVerifier = parse_EncryptionVerifier(blob, length);
	return o;
}
/* [MS-OFFCRYPTO] 2.3.6.1 RC4 Encryption Header */
function parse_RC4Header(blob, length) {
	var o = {};
	var vers = o.EncryptionVersionInfo = parse_Version(blob, 4); length -= 4;
	if(vers.Major != 1 || vers.Minor != 1) throw 'unrecognized version code ' + vers.Major + ' : ' + vers.Minor;
	o.Salt = blob.read_shift(16);
	o.EncryptedVerifier = blob.read_shift(16);
	o.EncryptedVerifierHash = blob.read_shift(16);
	return o;
}

/* 2.5.343 */
function parse_XORObfuscation(blob, length) {
	return { key: parseuint16(blob), verificationBytes: parseuint16(blob) };
}

/* 2.4.117 */
function parse_FilePassHeader(blob, length, oo) {
	var o = oo || {}; o.Info = blob.read_shift(2); blob.l -= 2;
	switch(o.Info) {
		case 1: o.Data = parse_RC4Header(blob, length); break;
		case 2: case 3: case 4: o.Data = parse_RC4CryptoHeader(blob, length); break;
		default: throw 'Unrecognized encryptionInfo: ' + o.Type;
	}
	return o;
}
function parse_FilePass(blob, length) {
	var o = { Type: blob.read_shift(2) }; /* wEncryptionType */
	switch(o.Type) {
		case 0: parse_XORObfuscation(blob, length-2, o); break;
		case 1: parse_FilePassHeader(blob, length-2, o); break;
		default: throw 'Unrecognized Encryption Type ' + o.Type;
	}
	return o;
}


/* Small helpers */
function parseread(l) { return function(blob, length) { blob.l+=l; return; }; }
function parseread1(blob, length) { blob.l+=1; return; }

/* Rgce Helpers */

/* 2.5.51 */
function parse_ColRelU(blob, length) {
	var c = blob.read_shift(2);
	return [c & 0x3FFF, (c >> 14) & 1, (c >> 15) & 1];
}

/* 2.5.198.105 */
function parse_RgceArea(blob, length) {
	var read = blob.read_shift.bind(blob);
	var r=read(2), R=read(2);
	var c=parse_ColRelU(blob, 2);
	var C=parse_ColRelU(blob, 2);
	return { s:{r:r, c:c[0], cRel:c[1], rRel:c[2]}, e:{r:R, c:C[0], cRel:C[1], rRel:C[2]} };
}

/* 2.5.198.105 TODO */
function parse_RgceAreaRel(blob, length) {
	var read = blob.read_shift.bind(blob);
	var r=read(2), R=read(2);
	var c=parse_ColRelU(blob, 2);
	var C=parse_ColRelU(blob, 2);
	return { s:{r:r, c:c[0], cRel:c[1], rRel:c[2]}, e:{r:R, c:C[0], cRel:C[1], rRel:C[2]} };
}

/* 2.5.198.109 */
function parse_RgceLoc(blob, length) {
	var r = blob.read_shift(2);
	var c = parse_ColRelU(blob, 2);
	return {r:r, c:c[0], cRel:c[1], rRel:c[2]};
}

/* 2.5.198.111 */
function parse_RgceLocRel(blob, length) {
	var r = blob.read_shift(2);
	var cl = blob.read_shift(2);
	var cRel = (cl & 0x8000) >> 15, rRel = (cl & 0x4000) >> 14;
	cl &= 0x3FFF;
	if(cRel !== 0) while(cl >= 0x100) cl -= 0x100;
	return {r:r,c:cl,cRel:cRel,rRel:rRel};
}

/* Ptg Tokens */

/* 2.5.198.27 */
function parse_PtgArea(blob, length) {
	var type = (blob[blob.l++] & 0x60) >> 5;
	var area = parse_RgceArea(blob, 8);
	return [type, area];
}

/* 2.5.198.28 */
function parse_PtgArea3d(blob, length) {
	var type = (blob[blob.l++] & 0x60) >> 5;
	var ixti = blob.read_shift(2);
	var area = parse_RgceArea(blob, 8);
	return [type, ixti, area];
}

/* 2.5.198.29 */
function parse_PtgAreaErr(blob, length) {
	var type = (blob[blob.l++] & 0x60) >> 5;
	blob.l += 8;
	return [type];
}
/* 2.5.198.30 */
function parse_PtgAreaErr3d(blob, length) {
	var type = (blob[blob.l++] & 0x60) >> 5;
	var ixti = blob.read_shift(2);
	blob.l += 8;
	return [type, ixti];
}

/* 2.5.198.31 */
function parse_PtgAreaN(blob, length) {
	var type = (blob[blob.l++] & 0x60) >> 5;
	var area = parse_RgceAreaRel(blob, 8);
	return [type, area];
}

/* 2.5.198.32 -- ignore this and look in PtgExtraArray for shape + values */
function parse_PtgArray(blob, length) {
	var type = (blob[blob.l++] & 0x60) >> 5;
	blob.l += 7;
	return [type];
}

/* 2.5.198.33 */
function parse_PtgAttrBaxcel(blob, length) {
	bitSemi = blob[blob.l+1] & 0x01; /* 1 = volatile */
	bitBaxcel = 1;
	blob.l += 4;
	return [bitSemi, bitBaxcel]
}

/* 2.5.198.34 */
function parse_PtgAttrChoose(blob, length) {
	blob.l +=2;
	var offset = blob.read_shift(2);
	var o = [];
	/* offset is 1 less than the number of elements */
	for(var i = 0; i <= offset; ++i) o.push(blob.read_shift(2));
	return o;
}

/* 2.5.198.35 */
function parse_PtgAttrGoto(blob, length) {
	bitGoto = (blob[blob.l+1] & 0xFF) ? 1 : 0;
	blob.l += 2;
	return [bitGoto, blob.read_shift(2)];
}

/* 2.5.198.36 */
function parse_PtgAttrIf(blob, length) {
	bitIf = (blob[blob.l+1] & 0xFF) ? 1 : 0;
	blob.l += 2;
	return [bitIf, blob.read_shift(2)];
}

/* 2.5.198.37 */
function parse_PtgAttrSemi(blob, length) {
	bitSemi = (blob[blob.l+1] & 0xFF) ? 1 : 0;
	blob.l += 4;
	return [bitSemi];
}

/* 2.5.198.40 (used by PtgAttrSpace and PtgAttrSpaceSemi) */
function parse_PtgAttrSpaceType(blob, length) {
	var type = blob.read_shift(1), cch = blob.read_shift(1);
	return [type, cch];
}

/* 2.5.198.38 */
function parse_PtgAttrSpace(blob, length) {
	blob.read_shift(2);
	return parse_PtgAttrSpaceType(blob, 2);
}

/* 2.5.198.39 */
function parse_PtgAttrSpaceSemi(blob, length) {
	blob.read_shift(2);
	return parse_PtgAttrSpaceType(blob, 2);
}

/* 2.5.198.84 TODO */
function parse_PtgRef(blob, length) {
	var ptg = blob[blob.l] & 0x1F;
	var type = (blob[blob.l] & 0x60)>>5;
	blob.l += 1;
	var loc = parse_RgceLoc(blob,4);
	return [type, loc];
}

/* 2.5.198.88 TODO */
function parse_PtgRefN(blob, length) {
	var ptg = blob[blob.l] & 0x1F;
	var type = (blob[blob.l] & 0x60)>>5;
	blob.l += 1;
	var loc = parse_RgceLocRel(blob,4);
	return [type, loc];
}

/* 2.5.198.85 TODO */
function parse_PtgRef3d(blob, length) {
	var ptg = blob[blob.l] & 0x1F;
	var type = (blob[blob.l] & 0x60)>>5;
	blob.l += 1;
	var ixti = blob.read_shift(2); // XtiIndex
	var loc = parse_RgceLoc(blob,4);
	return [type, ixti, loc];
}


/* 2.5.198.62 TODO */
function parse_PtgFunc(blob, length) {
	var ptg = blob[blob.l] & 0x1F;
	var type = (blob[blob.l] & 0x60)>>5;
	blob.l += 1;
	var iftab = blob.read_shift(2);
	return [FtabArgc[iftab], Ftab[iftab]];
}
/* 2.5.198.63 TODO */
function parse_PtgFuncVar(blob, length) {
	blob.l++;
	var cparams = blob.read_shift(1), tab = parsetab(blob);
	return [cparams, (tab[0] === 0 ? Ftab : Cetab)[tab[1]]];
}

function parsetab(blob, length) {
	return [blob[blob.l+1]>>7, blob.read_shift(2) & 0x7FFF];
}

/* 2.5.198.41 */
var parse_PtgAttrSum = parseread(4);
/* 2.5.198.43 */
var parse_PtgConcat = parseread1;

/* 2.5.198.58 */
function parse_PtgExp(blob, length) {
	blob.l++;
	var row = blob.read_shift(2);
	var col = blob.read_shift(2);
	return [row, col];
}

/* 2.5.198.57 */
function parse_PtgErr(blob, length) { blob.l++; return BERR[blob.read_shift(1)]; }

/* 2.5.198.66 TODO */
function parse_PtgInt(blob, length) { blob.l++; return blob.read_shift(2); }

/* 2.5.198.42 */
function parse_PtgBool(blob, length) { blob.l++; return blob.read_shift(1)!==0;}

/* 2.5.198.79 */
function parse_PtgNum(blob, length) { blob.l++; return parse_Xnum(blob, 8); }

/* 2.5.198.89 */
function parse_PtgStr(blob, length) { blob.l++; return parse_ShortXLUnicodeString(blob); }

/* 2.5.192.112 + 2.5.192.11{3,4,5,6,7} */
function parse_SerAr(blob) {
	var val = [];
	switch((val[0] = blob.read_shift(1))) {
		/* 2.5.192.113 */
		case 0x04: /* SerBool -- boolean */
			val[1] = parsebool(blob, 1) ? 'TRUE' : 'FALSE';
			blob.l += 7; break;
		/* 2.5.192.114 */
		case 0x10: /* SerErr -- error */
			val[1] = BERR[blob.l];
			blob.l += 8; break;
		/* 2.5.192.115 */
		case 0x00: /* SerNil -- honestly, I'm not sure how to reproduce this */
			blob.l += 8; break;
		/* 2.5.192.116 */
		case 0x01: /* SerNum -- Xnum */
			val[1] = parse_Xnum(blob, 8); break;
		/* 2.5.192.117 */
		case 0x02: /* SerStr -- XLUnicodeString (<256 chars) */
			val[1] = parse_XLUnicodeString(blob); break;
		default:
			throw "Bad SerAr: " + val[0];
	}
	return val;
}

/* 2.5.198.61 */
function parse_PtgExtraMem(blob, cce) {
	var count = blob.read_shift(2);
	var out = [];
	for(var i = 0; i != count; ++i) out.push(parse_Ref8U(blob, 8));
	return out;
}

/* 2.5.198.59 */
function parse_PtgExtraArray(blob) {
	var cols = 1 + blob.read_shift(1); //DColByteU
	var rows = 1 + blob.read_shift(2); //DRw
	for(var i = 0, o=[]; i != rows && (o[i] = []); ++i)
		for(var j = 0; j != cols; ++j) o[i][j] = parse_SerAr(blob);
	return o;
}

/* 2.5.198.76 */
function parse_PtgName(blob, length) {
	var type = (blob.read_shift(1) >>> 5) & 0x03;
	var nameindex = blob.read_shift(4);
	return [type, 0, nameindex];
}

/* 2.5.198.77 */
function parse_PtgNameX(blob, length) {
	var type = (blob.read_shift(1) >>> 5) & 0x03;
	var ixti = blob.read_shift(2); // XtiIndex
	var nameindex = blob.read_shift(4);
	return [type, ixti, nameindex];
}

/* 2.5.198.70 */
function parse_PtgMemArea(blob, length) {
	var type = (blob.read_shift(1) >>> 5) & 0x03;
	blob.l += 4;
	var cce = blob.read_shift(2);
	return [type, cce];
}

/* 2.5.198.72 */
function parse_PtgMemFunc(blob, length) {
	var type = (blob.read_shift(1) >>> 5) & 0x03;
	var cce = blob.read_shift(2);
	return [type, cce];
}


/* 2.5.198.86 */
function parse_PtgRefErr(blob, length) {
	var type = (blob.read_shift(1) >>> 5) & 0x03;
	blob.l += 4;
	return [type];
}

/* 2.5.198.26 */
var parse_PtgAdd = parseread1;
/* 2.5.198.45 */
var parse_PtgDiv = parseread1;
/* 2.5.198.56 */
var parse_PtgEq = parseread1;
/* 2.5.198.64 */
var parse_PtgGe = parseread1;
/* 2.5.198.65 */
var parse_PtgGt = parseread1;
/* 2.5.198.67 */
var parse_PtgIsect = parseread1;
/* 2.5.198.68 */
var parse_PtgLe = parseread1;
/* 2.5.198.69 */
var parse_PtgLt = parseread1;
/* 2.5.198.74 */
var parse_PtgMissArg = parseread1;
/* 2.5.198.75 */
var parse_PtgMul = parseread1;
/* 2.5.198.78 */
var parse_PtgNe = parseread1;
/* 2.5.198.80 */
var parse_PtgParen = parseread1;
/* 2.5.198.81 */
var parse_PtgPercent = parseread1;
/* 2.5.198.82 */
var parse_PtgPower = parseread1;
/* 2.5.198.83 */
var parse_PtgRange = parseread1;
/* 2.5.198.90 */
var parse_PtgSub = parseread1;
/* 2.5.198.93 */
var parse_PtgUminus = parseread1;
/* 2.5.198.94 */
var parse_PtgUnion = parseread1;
/* 2.5.198.95 */
var parse_PtgUplus = parseread1;

/* 2.5.198.71 */
var parse_PtgMemErr = parsenoop;
/* 2.5.198.73 */
var parse_PtgMemNoMem = parsenoop;
/* 2.5.198.87 */
var parse_PtgRefErr3d = parsenoop;
/* 2.5.198.92 */
var parse_PtgTbl = parsenoop;

/* 2.5.198.25 */
var PtgTypes = {
	0x01: { n:'PtgExp', f:parse_PtgExp },
	0x02: { n:'PtgTbl', f:parse_PtgTbl },
	0x03: { n:'PtgAdd', f:parse_PtgAdd },
	0x04: { n:'PtgSub', f:parse_PtgSub },
	0x05: { n:'PtgMul', f:parse_PtgMul },
	0x06: { n:'PtgDiv', f:parse_PtgDiv },
	0x07: { n:'PtgPower', f:parse_PtgPower },
	0x08: { n:'PtgConcat', f:parse_PtgConcat },
	0x09: { n:'PtgLt', f:parse_PtgLt },
	0x0A: { n:'PtgLe', f:parse_PtgLe },
	0x0B: { n:'PtgEq', f:parse_PtgEq },
	0x0C: { n:'PtgGe', f:parse_PtgGe },
	0x0D: { n:'PtgGt', f:parse_PtgGt },
	0x0E: { n:'PtgNe', f:parse_PtgNe },
	0x0F: { n:'PtgIsect', f:parse_PtgIsect },
	0x10: { n:'PtgUnion', f:parse_PtgUnion },
	0x11: { n:'PtgRange', f:parse_PtgRange },
	0x12: { n:'PtgUplus', f:parse_PtgUplus },
	0x13: { n:'PtgUminus', f:parse_PtgUminus },
	0x14: { n:'PtgPercent', f:parse_PtgPercent },
	0x15: { n:'PtgParen', f:parse_PtgParen },
	0x16: { n:'PtgMissArg', f:parse_PtgMissArg },
	0x17: { n:'PtgStr', f:parse_PtgStr },
	0x1C: { n:'PtgErr', f:parse_PtgErr },
	0x1D: { n:'PtgBool', f:parse_PtgBool },
	0x1E: { n:'PtgInt', f:parse_PtgInt },
	0x1F: { n:'PtgNum', f:parse_PtgNum },
	0x20: { n:'PtgArray', f:parse_PtgArray },
	0x21: { n:'PtgFunc', f:parse_PtgFunc },
	0x22: { n:'PtgFuncVar', f:parse_PtgFuncVar },
	0x23: { n:'PtgName', f:parse_PtgName },
	0x24: { n:'PtgRef', f:parse_PtgRef },
	0x25: { n:'PtgArea', f:parse_PtgArea },
	0x26: { n:'PtgMemArea', f:parse_PtgMemArea },
	0x27: { n:'PtgMemErr', f:parse_PtgMemErr },
	0x28: { n:'PtgMemNoMem', f:parse_PtgMemNoMem },
	0x29: { n:'PtgMemFunc', f:parse_PtgMemFunc },
	0x2A: { n:'PtgRefErr', f:parse_PtgRefErr },
	0x2B: { n:'PtgAreaErr', f:parse_PtgAreaErr },
	0x2C: { n:'PtgRefN', f:parse_PtgRefN },
	0x2D: { n:'PtgAreaN', f:parse_PtgAreaN },
	0x39: { n:'PtgNameX', f:parse_PtgNameX },
	0x3A: { n:'PtgRef3d', f:parse_PtgRef3d },
	0x3B: { n:'PtgArea3d', f:parse_PtgArea3d },
	0x3C: { n:'PtgRefErr3d', f:parse_PtgRefErr3d },
	0x3D: { n:'PtgAreaErr3d', f:parse_PtgAreaErr3d },
	0xFF: {}
};
/* These are duplicated in the PtgTypes table */
var PtgDupes = {
	0x40: 0x20, 0x60: 0x20,
	0x41: 0x21, 0x61: 0x21,
	0x42: 0x22, 0x62: 0x22,
	0x43: 0x23, 0x63: 0x23,
	0x44: 0x24, 0x64: 0x24,
	0x45: 0x25, 0x65: 0x25,
	0x46: 0x26, 0x66: 0x26,
	0x47: 0x27, 0x67: 0x27,
	0x48: 0x28, 0x68: 0x28,
	0x49: 0x29, 0x69: 0x29,
	0x4A: 0x2A, 0x6A: 0x2A,
	0x4B: 0x2B, 0x6B: 0x2B,
	0x4C: 0x2C, 0x6C: 0x2C,
	0x4D: 0x2D, 0x6D: 0x2D,
	0x59: 0x39, 0x79: 0x39,
	0x5A: 0x3A, 0x7A: 0x3A,
	0x5B: 0x3B, 0x7B: 0x3B,
	0x5C: 0x3C, 0x7C: 0x3C,
	0x5D: 0x3D, 0x7D: 0x3D
};
(function(){for(var y in PtgDupes) PtgTypes[y] = PtgTypes[PtgDupes[y]];})();

var Ptg18 = {};
var Ptg19 = {
	0x01: { n:'PtgAttrSemi', f:parse_PtgAttrSemi },
	0x02: { n:'PtgAttrIf', f:parse_PtgAttrIf },
	0x04: { n:'PtgAttrChoose', f:parse_PtgAttrChoose },
	0x08: { n:'PtgAttrGoto', f:parse_PtgAttrGoto },
	0x10: { n:'PtgAttrSum', f:parse_PtgAttrSum },
	0x20: { n:'PtgAttrBaxcel', f:parse_PtgAttrBaxcel },
	0x40: { n:'PtgAttrSpace', f:parse_PtgAttrSpace },
	0x41: { n:'PtgAttrSpaceSemi', f:parse_PtgAttrSpaceSemi },
	0xFF: {}
};

/* 2.4.127 TODO */
function parse_Formula(blob, length) {
	var cell = parse_Cell(blob, 6);
	var val = parse_FormulaValue(blob,8);
	var flags = blob.read_shift(1);
	blob.read_shift(1);
	var chn = blob.read_shift(4);
	var cbf = parse_CellParsedFormula(blob, length-20);
	return {cell:cell, val:val, formula:cbf, shared: (flags >> 3) & 1};
}

/* 2.5.133 */
function parse_FormulaValue(blob) {
	var b;
	if(blob.readUInt16LE(blob.l + 6) !== 0xFFFF) return parse_Xnum(blob);
	switch(blob[blob.l]) {
		case 0x00: blob.l += 8; return "String";
		case 0x01: b = blob[blob.l+2] === 0x1; blob.l += 8; return b;
		case 0x02: b = BERR[blob[blob.l+2]]; blob.l += 8; return b;
		case 0x03: blob.l += 8; return "";
	}
}

/* 2.5.198.103 */
function parse_RgbExtra(blob, length, rgce) {
	var target = blob.l + length;
	var o = [];
	for(var i = 0; i !== rgce.length; ++i) {
		switch(rgce[i][0]) {
			case 'PtgArray': /* PtgArray -> PtgExtraArray */
				rgce[i][1] = parse_PtgExtraArray(blob);
				o.push(rgce[i][1]);
				break;
			case 'PtgMemArea': /* PtgMemArea -> PtgExtraMem */
				rgce[i][2] = parse_PtgExtraMem(blob, rgce[i][1]);
				o.push(rgce[i][2]);
				break;
			default: break;
		}
	}
	length = target - blob.l;
	if(length !== 0) o.push(parsenoop(blob, length));
	return o;
}

/* 2.5.198.21 */
function parse_NameParsedFormula(blob, length, cce) {
	var target = blob.l + length;
	var rgce = parse_Rgce(blob, cce);
	var rgcb;
	if(target !== blob.l) rgcb = parse_RgbExtra(blob, target - blob.l, rgce);
	return [rgce, rgcb];
}

/* 2.5.198.3 TODO */
function parse_CellParsedFormula(blob, length) {
	var target = blob.l + length;
	var rgcb, cce = blob.read_shift(2); // length of rgce
	if(cce == 0xFFFF) return [[],parsenoop(blob, length-2)];
	var rgce = parse_Rgce(blob, cce);
	if(length !== cce + 2) rgcb = parse_RgbExtra(blob, length - cce - 2, rgce);
	return [rgce, rgcb];
}

/* 2.5.198.118 TODO */
function parse_SharedParsedFormula(blob, length) {
	var target = blob.l + length;
	var rgcb, cce = blob.read_shift(2); // length of rgce
	var rgce = parse_Rgce(blob, cce);
	if(cce == 0xFFFF) return [[],parsenoop(blob, length-2)];
	if(length !== cce + 2) rgcb = parse_RgbExtra(blob, target - cce - 2, rgce);
	return [rgce, rgcb];
}

/* 2.5.198.1 TODO */
function parse_ArrayParsedFormula(blob, length, opts, ref) {
	var target = blob.l + length;
	var rgcb, cce = blob.read_shift(2); // length of rgce
	if(cce == 0xFFFF) return [[],parsenoop(blob, length-2)];
	var rgce = parse_Rgce(blob, cce);
	if(length !== cce + 2) rgcb = parse_RgbExtra(blob, target - cce - 2, rgce);
	return [rgce, rgcb];
}

/* 2.5.198.104 */
function parse_Rgce(blob, length) {
	var target = blob.l + length;
	var R, id, ptgs = [];
	while(target != blob.l) {
		length = target - blob.l;
		id = blob[blob.l];
		R = PtgTypes[id];
		//console.log("ptg", id, R)
		if(id === 0x18 || id === 0x19) {
			id = blob[blob.l + 1];
			R = (id === 0x18 ? Ptg18 : Ptg19)[id];
		}
		if(!R || !R.f) { ptgs.push(parsenoop(blob, length)); }
		else { ptgs.push([R.n, R.f(blob, length)]); }
	}
	return ptgs;
}

/* 2.2.2 + Magic TODO */
function stringify_formula(formula, range, cell, supbooks) {
	range = range || {s:{c:0, r:0}};
	var stack = [], e1, e2, type, c, ixti, nameidx, r;
	if(!formula[0] || !formula[0][0]) return "";
	//console.log("--",cell,formula[0])
	formula[0].forEach(function(f) {
		//console.log("++",f, stack)
		switch(f[0]) {
		/* 2.2.2.1 Unary Operator Tokens */
			/* 2.5.198.93 */
			case 'PtgUminus': stack.push("-" + stack.pop()); break;
			/* 2.5.198.95 */
			case 'PtgUplus': stack.push("+" + stack.pop()); break;
			/* 2.5.198.81 */
			case 'PtgPercent': stack.push(stack.pop() + "%"); break;

		/* 2.2.2.1 Binary Value Operator Token */
			/* 2.5.198.26 */
			case 'PtgAdd':
				e1 = stack.pop(); e2 = stack.pop();
				stack.push(e2+"+"+e1);
				break;
			/* 2.5.198.90 */
			case 'PtgSub':
				e1 = stack.pop(); e2 = stack.pop();
				stack.push(e2+"-"+e1);
				break;
			/* 2.5.198.75 */
			case 'PtgMul':
				e1 = stack.pop(); e2 = stack.pop();
				stack.push(e2+"*"+e1);
				break;
			/* 2.5.198.45 */
			case 'PtgDiv':
				e1 = stack.pop(); e2 = stack.pop();
				stack.push(e2+"/"+e1);
				break;
			/* 2.5.198.82 */
			case 'PtgPower':
				e1 = stack.pop(); e2 = stack.pop();
				stack.push(e2+"^"+e1);
				break;
			/* 2.5.198.43 */
			case 'PtgConcat':
				e1 = stack.pop(); e2 = stack.pop();
				stack.push(e2+"&"+e1);
				break;
			/* 2.5.198.69 */
			case 'PtgLt':
				e1 = stack.pop(); e2 = stack.pop();
				stack.push(e2+"<"+e1);
				break;
			/* 2.5.198.68 */
			case 'PtgLe':
				e1 = stack.pop(); e2 = stack.pop();
				stack.push(e2+"<="+e1);
				break;
			/* 2.5.198.56 */
			case 'PtgEq':
				e1 = stack.pop(); e2 = stack.pop();
				stack.push(e2+"="+e1);
				break;
			/* 2.5.198.64 */
			case 'PtgGe':
				e1 = stack.pop(); e2 = stack.pop();
				stack.push(e2+">="+e1);
				break;
			/* 2.5.198.65 */
			case 'PtgGt':
				e1 = stack.pop(); e2 = stack.pop();
				stack.push(e2+">"+e1);
				break;
			/* 2.5.198.78 */
			case 'PtgNe':
				e1 = stack.pop(); e2 = stack.pop();
				stack.push(e2+"<>"+e1);
				break;

		/* 2.2.2.1 Binary Reference Operator Token */
			/* 2.5.198.67 */
			case 'PtgIsect':
				e1 = stack.pop(); e2 = stack.pop();
				stack.push(e2+" "+e1);
				break;
			case 'PtgUnion':
				e1 = stack.pop(); e2 = stack.pop();
				stack.push(e2+","+e1);
				break;
			case 'PtgRange': break;

		/* 2.2.2.3 Control Tokens "can be ignored" */
			/* 2.5.198.34 */
			case 'PtgAttrChoose': break;
			/* 2.5.198.35 */
			case 'PtgAttrGoto': break;
			/* 2.5.198.36 */
			case 'PtgAttrIf': break;


			/* 2.5.198.84 */
			case 'PtgRef':
				type = f[1][0]; c = shift_cell(decode_cell(encode_cell(f[1][1])), range);
				stack.push(encode_cell(c));
				break;
			/* 2.5.198.88 */
			case 'PtgRefN':
				type = f[1][0]; c = shift_cell(decode_cell(encode_cell(f[1][1])), cell);
				stack.push(encode_cell(c));
				break;
			case 'PtgRef3d': // TODO: lots of stuff
				type = f[1][0]; ixti = f[1][1]; c = shift_cell(f[1][2], range);
				stack.push(supbooks[1][ixti+1]+"!"+encode_cell(c));
				break;

		/* Function Call */
			/* 2.5.198.62 */
			case 'PtgFunc':
			/* 2.5.198.63 */
			case 'PtgFuncVar':
				/* f[1] = [argc, func] */
				var argc = f[1][0], func = f[1][1];
				if(!argc) argc = 0;
				var args = stack.slice(-argc);
				stack.length -= argc;
				if(func === 'User') func = args.shift();
				stack.push(func + "(" + args.join(",") + ")");
				break;

			/* 2.5.198.42 */
			case 'PtgBool': stack.push(f[1] ? "TRUE" : "FALSE"); break;
			/* 2.5.198.66 */
			case 'PtgInt': stack.push(f[1]); break;
			/* 2.5.198.79 TODO: precision? */
			case 'PtgNum': stack.push(String(f[1])); break;
			/* 2.5.198.89 */
			case 'PtgStr': stack.push('"' + f[1] + '"'); break;
			/* 2.5.198.57 */
			case 'PtgErr': stack.push(f[1]); break;
			/* 2.5.198.27 TODO: fixed points */
			case 'PtgArea':
				type = f[1][0]; r = shift_range(f[1][1], range);
				stack.push(encode_range(r));
				break;
			/* 2.5.198.28 */
			case 'PtgArea3d': // TODO: lots of stuff
				type = f[1][0]; ixti = f[1][1]; r = f[1][2];
				stack.push(supbooks[1][ixti+1]+"!"+encode_range(r));
				break;
			/* 2.5.198.41 */
			case 'PtgAttrSum':
				stack.push("SUM(" + stack.pop() + ")");
				break;

		/* Expression Prefixes */
			/* 2.5.198.37 */
			case 'PtgAttrSemi': break;

			/* 2.5.97.60 TODO: do something different for revisions */
			case 'PtgName':
				/* f[1] = type, 0, nameindex */
				nameidx = f[1][2];
				var lbl = supbooks[0][nameidx];
				var name = lbl.Name;
				if(name in XLSXFutureFunctions) name = XLSXFutureFunctions[name];
				stack.push(name);
				break;

			/* 2.5.97.61 TODO: do something different for revisions */
			case 'PtgNameX':
				/* f[1] = type, ixti, nameindex */
				var bookidx = f[1][1]; nameidx = f[1][2]; var externbook;
				/* TODO: Properly handle missing values */
				if(supbooks[bookidx+1]) externbook = supbooks[bookidx+1][nameidx];
				else if(supbooks[bookidx-1]) externbook = supbooks[bookidx-1][nameidx];
				if(!externbook) externbook = {body: "??NAMEX??"};
				stack.push(externbook.body);
				break;

		/* 2.2.2.4 Display Tokens */
			/* 2.5.198.80 */
			case 'PtgParen': stack.push('(' + stack.pop() + ')'); break;

			/* 2.5.198.86 */
			case 'PtgRefErr': stack.push('#REF!'); break;

		/* */
			/* 2.5.198.58 TODO */
			case 'PtgExp':
				c = {c:f[1][1],r:f[1][0]};
				if(supbooks.sharedf[encode_cell(c)]) {
					var parsedf = (supbooks.sharedf[encode_cell(c)]);
					var q = {c: cell.c, r:cell.r};
					stack.push(stringify_formula(parsedf, range, q, supbooks));
				}
				else stack.push(f[1]);
				break;

			/* 2.5.198.32 TODO */
			case 'PtgArray':
				stack.push("{" + f[1].map(function(x) { return x.map(function(y) { return y[1];}).join(",");}).join(";") + "}");
				break;

		/* 2.2.2.5 Mem Tokens */
			/* 2.5.198.70 TODO: confirm this is a non-display */
			case 'PtgMemArea':
				//stack.push("(" + f[2].map(encode_range).join(",") + ")");
				break;

			/* 2.5.198.38 TODO */
			case 'PtgAttrSpace': break;

			/* 2.5.198.92 TODO */
			case 'PtgTbl': break;

			/* 2.5.198.71 */
			case 'PtgMemErr': break;

			/* 2.5.198.74 */
			case 'PtgMissArg':
				stack.push("");
				break;

			/* 2.5.198.29 TODO */
			case 'PtgAreaErr': break;

			/* 2.5.198.31 TODO */
			case 'PtgAreaN': stack.push(""); break;

			/* 2.5.198.87 TODO */
			case 'PtgRefErr3d': break;

			/* 2.5.198.72 TODO */
			case 'PtgMemFunc': break;

			default: throw 'Unrecognized Formula Token: ' + f;
		}
		//console.log("::",f, stack)
	});
	//console.log("--",stack);
	return stack[0];
}
/* 2.5.198.44 */
var PtgDataType = {
	0x1: "REFERENCE", // reference to range
	0x2: "VALUE", // single value
	0x3: "ARRAY" // array of values
};

/* 2.5.198.2 */
var BERR = {
	0x00: "#NULL!",
	0x07: "#DIV/0!",
	0x0F: "#VALUE!",
	0x17: "#REF!",
	0x1D: "#NAME?",
	0x24: "#NUM!",
	0x2A: "#N/A",
	0x2B: "#GETTING_DATA", /* Noted in 2.5.10 but not in 2.5.198.2 */
	0xFF: "#WTF?"
};

/* 2.5.198.4 */
var Cetab = {
	0x0000: 'BEEP',
	0x0001: 'OPEN',
	0x0002: 'OPEN.LINKS',
	0x0003: 'CLOSE.ALL',
	0x0004: 'SAVE',
	0x0005: 'SAVE.AS',
	0x0006: 'FILE.DELETE',
	0x0007: 'PAGE.SETUP',
	0x0008: 'PRINT',
	0x0009: 'PRINTER.SETUP',
	0x000A: 'QUIT',
	0x000B: 'NEW.WINDOW',
	0x000C: 'ARRANGE.ALL',
	0x000D: 'WINDOW.SIZE',
	0x000E: 'WINDOW.MOVE',
	0x000F: 'FULL',
	0x0010: 'CLOSE',
	0x0011: 'RUN',
	0x0016: 'SET.PRINT.AREA',
	0x0017: 'SET.PRINT.TITLES',
	0x0018: 'SET.PAGE.BREAK',
	0x0019: 'REMOVE.PAGE.BREAK',
	0x001A: 'FONT',
	0x001B: 'DISPLAY',
	0x001C: 'PROTECT.DOCUMENT',
	0x001D: 'PRECISION',
	0x001E: 'A1.R1C1',
	0x001F: 'CALCULATE.NOW',
	0x0020: 'CALCULATION',
	0x0022: 'DATA.FIND',
	0x0023: 'EXTRACT',
	0x0024: 'DATA.DELETE',
	0x0025: 'SET.DATABASE',
	0x0026: 'SET.CRITERIA',
	0x0027: 'SORT',
	0x0028: 'DATA.SERIES',
	0x0029: 'TABLE',
	0x002A: 'FORMAT.NUMBER',
	0x002B: 'ALIGNMENT',
	0x002C: 'STYLE',
	0x002D: 'BORDER',
	0x002E: 'CELL.PROTECTION',
	0x002F: 'COLUMN.WIDTH',
	0x0030: 'UNDO',
	0x0031: 'CUT',
	0x0032: 'COPY',
	0x0033: 'PASTE',
	0x0034: 'CLEAR',
	0x0035: 'PASTE.SPECIAL',
	0x0036: 'EDIT.DELETE',
	0x0037: 'INSERT',
	0x0038: 'FILL.RIGHT',
	0x0039: 'FILL.DOWN',
	0x003D: 'DEFINE.NAME',
	0x003E: 'CREATE.NAMES',
	0x003F: 'FORMULA.GOTO',
	0x0040: 'FORMULA.FIND',
	0x0041: 'SELECT.LAST.CELL',
	0x0042: 'SHOW.ACTIVE.CELL',
	0x0043: 'GALLERY.AREA',
	0x0044: 'GALLERY.BAR',
	0x0045: 'GALLERY.COLUMN',
	0x0046: 'GALLERY.LINE',
	0x0047: 'GALLERY.PIE',
	0x0048: 'GALLERY.SCATTER',
	0x0049: 'COMBINATION',
	0x004A: 'PREFERRED',
	0x004B: 'ADD.OVERLAY',
	0x004C: 'GRIDLINES',
	0x004D: 'SET.PREFERRED',
	0x004E: 'AXES',
	0x004F: 'LEGEND',
	0x0050: 'ATTACH.TEXT',
	0x0051: 'ADD.ARROW',
	0x0052: 'SELECT.CHART',
	0x0053: 'SELECT.PLOT.AREA',
	0x0054: 'PATTERNS',
	0x0055: 'MAIN.CHART',
	0x0056: 'OVERLAY',
	0x0057: 'SCALE',
	0x0058: 'FORMAT.LEGEND',
	0x0059: 'FORMAT.TEXT',
	0x005A: 'EDIT.REPEAT',
	0x005B: 'PARSE',
	0x005C: 'JUSTIFY',
	0x005D: 'HIDE',
	0x005E: 'UNHIDE',
	0x005F: 'WORKSPACE',
	0x0060: 'FORMULA',
	0x0061: 'FORMULA.FILL',
	0x0062: 'FORMULA.ARRAY',
	0x0063: 'DATA.FIND.NEXT',
	0x0064: 'DATA.FIND.PREV',
	0x0065: 'FORMULA.FIND.NEXT',
	0x0066: 'FORMULA.FIND.PREV',
	0x0067: 'ACTIVATE',
	0x0068: 'ACTIVATE.NEXT',
	0x0069: 'ACTIVATE.PREV',
	0x006A: 'UNLOCKED.NEXT',
	0x006B: 'UNLOCKED.PREV',
	0x006C: 'COPY.PICTURE',
	0x006D: 'SELECT',
	0x006E: 'DELETE.NAME',
	0x006F: 'DELETE.FORMAT',
	0x0070: 'VLINE',
	0x0071: 'HLINE',
	0x0072: 'VPAGE',
	0x0073: 'HPAGE',
	0x0074: 'VSCROLL',
	0x0075: 'HSCROLL',
	0x0076: 'ALERT',
	0x0077: 'NEW',
	0x0078: 'CANCEL.COPY',
	0x0079: 'SHOW.CLIPBOARD',
	0x007A: 'MESSAGE',
	0x007C: 'PASTE.LINK',
	0x007D: 'APP.ACTIVATE',
	0x007E: 'DELETE.ARROW',
	0x007F: 'ROW.HEIGHT',
	0x0080: 'FORMAT.MOVE',
	0x0081: 'FORMAT.SIZE',
	0x0082: 'FORMULA.REPLACE',
	0x0083: 'SEND.KEYS',
	0x0084: 'SELECT.SPECIAL',
	0x0085: 'APPLY.NAMES',
	0x0086: 'REPLACE.FONT',
	0x0087: 'FREEZE.PANES',
	0x0088: 'SHOW.INFO',
	0x0089: 'SPLIT',
	0x008A: 'ON.WINDOW',
	0x008B: 'ON.DATA',
	0x008C: 'DISABLE.INPUT',
	0x008E: 'OUTLINE',
	0x008F: 'LIST.NAMES',
	0x0090: 'FILE.CLOSE',
	0x0091: 'SAVE.WORKBOOK',
	0x0092: 'DATA.FORM',
	0x0093: 'COPY.CHART',
	0x0094: 'ON.TIME',
	0x0095: 'WAIT',
	0x0096: 'FORMAT.FONT',
	0x0097: 'FILL.UP',
	0x0098: 'FILL.LEFT',
	0x0099: 'DELETE.OVERLAY',
	0x009B: 'SHORT.MENUS',
	0x009F: 'SET.UPDATE.STATUS',
	0x00A1: 'COLOR.PALETTE',
	0x00A2: 'DELETE.STYLE',
	0x00A3: 'WINDOW.RESTORE',
	0x00A4: 'WINDOW.MAXIMIZE',
	0x00A6: 'CHANGE.LINK',
	0x00A7: 'CALCULATE.DOCUMENT',
	0x00A8: 'ON.KEY',
	0x00A9: 'APP.RESTORE',
	0x00AA: 'APP.MOVE',
	0x00AB: 'APP.SIZE',
	0x00AC: 'APP.MINIMIZE',
	0x00AD: 'APP.MAXIMIZE',
	0x00AE: 'BRING.TO.FRONT',
	0x00AF: 'SEND.TO.BACK',
	0x00B9: 'MAIN.CHART.TYPE',
	0x00BA: 'OVERLAY.CHART.TYPE',
	0x00BB: 'SELECT.END',
	0x00BC: 'OPEN.MAIL',
	0x00BD: 'SEND.MAIL',
	0x00BE: 'STANDARD.FONT',
	0x00BF: 'CONSOLIDATE',
	0x00C0: 'SORT.SPECIAL',
	0x00C1: 'GALLERY.3D.AREA',
	0x00C2: 'GALLERY.3D.COLUMN',
	0x00C3: 'GALLERY.3D.LINE',
	0x00C4: 'GALLERY.3D.PIE',
	0x00C5: 'VIEW.3D',
	0x00C6: 'GOAL.SEEK',
	0x00C7: 'WORKGROUP',
	0x00C8: 'FILL.GROUP',
	0x00C9: 'UPDATE.LINK',
	0x00CA: 'PROMOTE',
	0x00CB: 'DEMOTE',
	0x00CC: 'SHOW.DETAIL',
	0x00CE: 'UNGROUP',
	0x00CF: 'OBJECT.PROPERTIES',
	0x00D0: 'SAVE.NEW.OBJECT',
	0x00D1: 'SHARE',
	0x00D2: 'SHARE.NAME',
	0x00D3: 'DUPLICATE',
	0x00D4: 'APPLY.STYLE',
	0x00D5: 'ASSIGN.TO.OBJECT',
	0x00D6: 'OBJECT.PROTECTION',
	0x00D7: 'HIDE.OBJECT',
	0x00D8: 'SET.EXTRACT',
	0x00D9: 'CREATE.PUBLISHER',
	0x00DA: 'SUBSCRIBE.TO',
	0x00DB: 'ATTRIBUTES',
	0x00DC: 'SHOW.TOOLBAR',
	0x00DE: 'PRINT.PREVIEW',
	0x00DF: 'EDIT.COLOR',
	0x00E0: 'SHOW.LEVELS',
	0x00E1: 'FORMAT.MAIN',
	0x00E2: 'FORMAT.OVERLAY',
	0x00E3: 'ON.RECALC',
	0x00E4: 'EDIT.SERIES',
	0x00E5: 'DEFINE.STYLE',
	0x00F0: 'LINE.PRINT',
	0x00F3: 'ENTER.DATA',
	0x00F9: 'GALLERY.RADAR',
	0x00FA: 'MERGE.STYLES',
	0x00FB: 'EDITION.OPTIONS',
	0x00FC: 'PASTE.PICTURE',
	0x00FD: 'PASTE.PICTURE.LINK',
	0x00FE: 'SPELLING',
	0x0100: 'ZOOM',
	0x0103: 'INSERT.OBJECT',
	0x0104: 'WINDOW.MINIMIZE',
	0x0109: 'SOUND.NOTE',
	0x010A: 'SOUND.PLAY',
	0x010B: 'FORMAT.SHAPE',
	0x010C: 'EXTEND.POLYGON',
	0x010D: 'FORMAT.AUTO',
	0x0110: 'GALLERY.3D.BAR',
	0x0111: 'GALLERY.3D.SURFACE',
	0x0112: 'FILL.AUTO',
	0x0114: 'CUSTOMIZE.TOOLBAR',
	0x0115: 'ADD.TOOL',
	0x0116: 'EDIT.OBJECT',
	0x0117: 'ON.DOUBLECLICK',
	0x0118: 'ON.ENTRY',
	0x0119: 'WORKBOOK.ADD',
	0x011A: 'WORKBOOK.MOVE',
	0x011B: 'WORKBOOK.COPY',
	0x011C: 'WORKBOOK.OPTIONS',
	0x011D: 'SAVE.WORKSPACE',
	0x0120: 'CHART.WIZARD',
	0x0121: 'DELETE.TOOL',
	0x0122: 'MOVE.TOOL',
	0x0123: 'WORKBOOK.SELECT',
	0x0124: 'WORKBOOK.ACTIVATE',
	0x0125: 'ASSIGN.TO.TOOL',
	0x0127: 'COPY.TOOL',
	0x0128: 'RESET.TOOL',
	0x0129: 'CONSTRAIN.NUMERIC',
	0x012A: 'PASTE.TOOL',
	0x012E: 'WORKBOOK.NEW',
	0x0131: 'SCENARIO.CELLS',
	0x0132: 'SCENARIO.DELETE',
	0x0133: 'SCENARIO.ADD',
	0x0134: 'SCENARIO.EDIT',
	0x0135: 'SCENARIO.SHOW',
	0x0136: 'SCENARIO.SHOW.NEXT',
	0x0137: 'SCENARIO.SUMMARY',
	0x0138: 'PIVOT.TABLE.WIZARD',
	0x0139: 'PIVOT.FIELD.PROPERTIES',
	0x013A: 'PIVOT.FIELD',
	0x013B: 'PIVOT.ITEM',
	0x013C: 'PIVOT.ADD.FIELDS',
	0x013E: 'OPTIONS.CALCULATION',
	0x013F: 'OPTIONS.EDIT',
	0x0140: 'OPTIONS.VIEW',
	0x0141: 'ADDIN.MANAGER',
	0x0142: 'MENU.EDITOR',
	0x0143: 'ATTACH.TOOLBARS',
	0x0144: 'VBAActivate',
	0x0145: 'OPTIONS.CHART',
	0x0148: 'VBA.INSERT.FILE',
	0x014A: 'VBA.PROCEDURE.DEFINITION',
	0x0150: 'ROUTING.SLIP',
	0x0152: 'ROUTE.DOCUMENT',
	0x0153: 'MAIL.LOGON',
	0x0156: 'INSERT.PICTURE',
	0x0157: 'EDIT.TOOL',
	0x0158: 'GALLERY.DOUGHNUT',
	0x015E: 'CHART.TREND',
	0x0160: 'PIVOT.ITEM.PROPERTIES',
	0x0162: 'WORKBOOK.INSERT',
	0x0163: 'OPTIONS.TRANSITION',
	0x0164: 'OPTIONS.GENERAL',
	0x0172: 'FILTER.ADVANCED',
	0x0175: 'MAIL.ADD.MAILER',
	0x0176: 'MAIL.DELETE.MAILER',
	0x0177: 'MAIL.REPLY',
	0x0178: 'MAIL.REPLY.ALL',
	0x0179: 'MAIL.FORWARD',
	0x017A: 'MAIL.NEXT.LETTER',
	0x017B: 'DATA.LABEL',
	0x017C: 'INSERT.TITLE',
	0x017D: 'FONT.PROPERTIES',
	0x017E: 'MACRO.OPTIONS',
	0x017F: 'WORKBOOK.HIDE',
	0x0180: 'WORKBOOK.UNHIDE',
	0x0181: 'WORKBOOK.DELETE',
	0x0182: 'WORKBOOK.NAME',
	0x0184: 'GALLERY.CUSTOM',
	0x0186: 'ADD.CHART.AUTOFORMAT',
	0x0187: 'DELETE.CHART.AUTOFORMAT',
	0x0188: 'CHART.ADD.DATA',
	0x0189: 'AUTO.OUTLINE',
	0x018A: 'TAB.ORDER',
	0x018B: 'SHOW.DIALOG',
	0x018C: 'SELECT.ALL',
	0x018D: 'UNGROUP.SHEETS',
	0x018E: 'SUBTOTAL.CREATE',
	0x018F: 'SUBTOTAL.REMOVE',
	0x0190: 'RENAME.OBJECT',
	0x019C: 'WORKBOOK.SCROLL',
	0x019D: 'WORKBOOK.NEXT',
	0x019E: 'WORKBOOK.PREV',
	0x019F: 'WORKBOOK.TAB.SPLIT',
	0x01A0: 'FULL.SCREEN',
	0x01A1: 'WORKBOOK.PROTECT',
	0x01A4: 'SCROLLBAR.PROPERTIES',
	0x01A5: 'PIVOT.SHOW.PAGES',
	0x01A6: 'TEXT.TO.COLUMNS',
	0x01A7: 'FORMAT.CHARTTYPE',
	0x01A8: 'LINK.FORMAT',
	0x01A9: 'TRACER.DISPLAY',
	0x01AE: 'TRACER.NAVIGATE',
	0x01AF: 'TRACER.CLEAR',
	0x01B0: 'TRACER.ERROR',
	0x01B1: 'PIVOT.FIELD.GROUP',
	0x01B2: 'PIVOT.FIELD.UNGROUP',
	0x01B3: 'CHECKBOX.PROPERTIES',
	0x01B4: 'LABEL.PROPERTIES',
	0x01B5: 'LISTBOX.PROPERTIES',
	0x01B6: 'EDITBOX.PROPERTIES',
	0x01B7: 'PIVOT.REFRESH',
	0x01B8: 'LINK.COMBO',
	0x01B9: 'OPEN.TEXT',
	0x01BA: 'HIDE.DIALOG',
	0x01BB: 'SET.DIALOG.FOCUS',
	0x01BC: 'ENABLE.OBJECT',
	0x01BD: 'PUSHBUTTON.PROPERTIES',
	0x01BE: 'SET.DIALOG.DEFAULT',
	0x01BF: 'FILTER',
	0x01C0: 'FILTER.SHOW.ALL',
	0x01C1: 'CLEAR.OUTLINE',
	0x01C2: 'FUNCTION.WIZARD',
	0x01C3: 'ADD.LIST.ITEM',
	0x01C4: 'SET.LIST.ITEM',
	0x01C5: 'REMOVE.LIST.ITEM',
	0x01C6: 'SELECT.LIST.ITEM',
	0x01C7: 'SET.CONTROL.VALUE',
	0x01C8: 'SAVE.COPY.AS',
	0x01CA: 'OPTIONS.LISTS.ADD',
	0x01CB: 'OPTIONS.LISTS.DELETE',
	0x01CC: 'SERIES.AXES',
	0x01CD: 'SERIES.X',
	0x01CE: 'SERIES.Y',
	0x01CF: 'ERRORBAR.X',
	0x01D0: 'ERRORBAR.Y',
	0x01D1: 'FORMAT.CHART',
	0x01D2: 'SERIES.ORDER',
	0x01D3: 'MAIL.LOGOFF',
	0x01D4: 'CLEAR.ROUTING.SLIP',
	0x01D5: 'APP.ACTIVATE.MICROSOFT',
	0x01D6: 'MAIL.EDIT.MAILER',
	0x01D7: 'ON.SHEET',
	0x01D8: 'STANDARD.WIDTH',
	0x01D9: 'SCENARIO.MERGE',
	0x01DA: 'SUMMARY.INFO',
	0x01DB: 'FIND.FILE',
	0x01DC: 'ACTIVE.CELL.FONT',
	0x01DD: 'ENABLE.TIPWIZARD',
	0x01DE: 'VBA.MAKE.ADDIN',
	0x01E0: 'INSERTDATATABLE',
	0x01E1: 'WORKGROUP.OPTIONS',
	0x01E2: 'MAIL.SEND.MAILER',
	0x01E5: 'AUTOCORRECT',
	0x01E9: 'POST.DOCUMENT',
	0x01EB: 'PICKLIST',
	0x01ED: 'VIEW.SHOW',
	0x01EE: 'VIEW.DEFINE',
	0x01EF: 'VIEW.DELETE',
	0x01FD: 'SHEET.BACKGROUND',
	0x01FE: 'INSERT.MAP.OBJECT',
	0x01FF: 'OPTIONS.MENONO',
	0x0205: 'MSOCHECKS',
	0x0206: 'NORMAL',
	0x0207: 'LAYOUT',
	0x0208: 'RM.PRINT.AREA',
	0x0209: 'CLEAR.PRINT.AREA',
	0x020A: 'ADD.PRINT.AREA',
	0x020B: 'MOVE.BRK',
	0x0221: 'HIDECURR.NOTE',
	0x0222: 'HIDEALL.NOTES',
	0x0223: 'DELETE.NOTE',
	0x0224: 'TRAVERSE.NOTES',
	0x0225: 'ACTIVATE.NOTES',
	0x026C: 'PROTECT.REVISIONS',
	0x026D: 'UNPROTECT.REVISIONS',
	0x0287: 'OPTIONS.ME',
	0x028D: 'WEB.PUBLISH',
	0x029B: 'NEWWEBQUERY',
	0x02A1: 'PIVOT.TABLE.CHART',
	0x02F1: 'OPTIONS.SAVE',
	0x02F3: 'OPTIONS.SPELL',
	0x0328: 'HIDEALL.INKANNOTS'
};

/* 2.5.198.17 */
var Ftab = {
	0x0000: 'COUNT',
	0x0001: 'IF',
	0x0002: 'ISNA',
	0x0003: 'ISERROR',
	0x0004: 'SUM',
	0x0005: 'AVERAGE',
	0x0006: 'MIN',
	0x0007: 'MAX',
	0x0008: 'ROW',
	0x0009: 'COLUMN',
	0x000A: 'NA',
	0x000B: 'NPV',
	0x000C: 'STDEV',
	0x000D: 'DOLLAR',
	0x000E: 'FIXED',
	0x000F: 'SIN',
	0x0010: 'COS',
	0x0011: 'TAN',
	0x0012: 'ATAN',
	0x0013: 'PI',
	0x0014: 'SQRT',
	0x0015: 'EXP',
	0x0016: 'LN',
	0x0017: 'LOG10',
	0x0018: 'ABS',
	0x0019: 'INT',
	0x001A: 'SIGN',
	0x001B: 'ROUND',
	0x001C: 'LOOKUP',
	0x001D: 'INDEX',
	0x001E: 'REPT',
	0x001F: 'MID',
	0x0020: 'LEN',
	0x0021: 'VALUE',
	0x0022: 'TRUE',
	0x0023: 'FALSE',
	0x0024: 'AND',
	0x0025: 'OR',
	0x0026: 'NOT',
	0x0027: 'MOD',
	0x0028: 'DCOUNT',
	0x0029: 'DSUM',
	0x002A: 'DAVERAGE',
	0x002B: 'DMIN',
	0x002C: 'DMAX',
	0x002D: 'DSTDEV',
	0x002E: 'VAR',
	0x002F: 'DVAR',
	0x0030: 'TEXT',
	0x0031: 'LINEST',
	0x0032: 'TREND',
	0x0033: 'LOGEST',
	0x0034: 'GROWTH',
	0x0035: 'GOTO',
	0x0036: 'HALT',
	0x0037: 'RETURN',
	0x0038: 'PV',
	0x0039: 'FV',
	0x003A: 'NPER',
	0x003B: 'PMT',
	0x003C: 'RATE',
	0x003D: 'MIRR',
	0x003E: 'IRR',
	0x003F: 'RAND',
	0x0040: 'MATCH',
	0x0041: 'DATE',
	0x0042: 'TIME',
	0x0043: 'DAY',
	0x0044: 'MONTH',
	0x0045: 'YEAR',
	0x0046: 'WEEKDAY',
	0x0047: 'HOUR',
	0x0048: 'MINUTE',
	0x0049: 'SECOND',
	0x004A: 'NOW',
	0x004B: 'AREAS',
	0x004C: 'ROWS',
	0x004D: 'COLUMNS',
	0x004E: 'OFFSET',
	0x004F: 'ABSREF',
	0x0050: 'RELREF',
	0x0051: 'ARGUMENT',
	0x0052: 'SEARCH',
	0x0053: 'TRANSPOSE',
	0x0054: 'ERROR',
	0x0055: 'STEP',
	0x0056: 'TYPE',
	0x0057: 'ECHO',
	0x0058: 'SET.NAME',
	0x0059: 'CALLER',
	0x005A: 'DEREF',
	0x005B: 'WINDOWS',
	0x005C: 'SERIES',
	0x005D: 'DOCUMENTS',
	0x005E: 'ACTIVE.CELL',
	0x005F: 'SELECTION',
	0x0060: 'RESULT',
	0x0061: 'ATAN2',
	0x0062: 'ASIN',
	0x0063: 'ACOS',
	0x0064: 'CHOOSE',
	0x0065: 'HLOOKUP',
	0x0066: 'VLOOKUP',
	0x0067: 'LINKS',
	0x0068: 'INPUT',
	0x0069: 'ISREF',
	0x006A: 'GET.FORMULA',
	0x006B: 'GET.NAME',
	0x006C: 'SET.VALUE',
	0x006D: 'LOG',
	0x006E: 'EXEC',
	0x006F: 'CHAR',
	0x0070: 'LOWER',
	0x0071: 'UPPER',
	0x0072: 'PROPER',
	0x0073: 'LEFT',
	0x0074: 'RIGHT',
	0x0075: 'EXACT',
	0x0076: 'TRIM',
	0x0077: 'REPLACE',
	0x0078: 'SUBSTITUTE',
	0x0079: 'CODE',
	0x007A: 'NAMES',
	0x007B: 'DIRECTORY',
	0x007C: 'FIND',
	0x007D: 'CELL',
	0x007E: 'ISERR',
	0x007F: 'ISTEXT',
	0x0080: 'ISNUMBER',
	0x0081: 'ISBLANK',
	0x0082: 'T',
	0x0083: 'N',
	0x0084: 'FOPEN',
	0x0085: 'FCLOSE',
	0x0086: 'FSIZE',
	0x0087: 'FREADLN',
	0x0088: 'FREAD',
	0x0089: 'FWRITELN',
	0x008A: 'FWRITE',
	0x008B: 'FPOS',
	0x008C: 'DATEVALUE',
	0x008D: 'TIMEVALUE',
	0x008E: 'SLN',
	0x008F: 'SYD',
	0x0090: 'DDB',
	0x0091: 'GET.DEF',
	0x0092: 'REFTEXT',
	0x0093: 'TEXTREF',
	0x0094: 'INDIRECT',
	0x0095: 'REGISTER',
	0x0096: 'CALL',
	0x0097: 'ADD.BAR',
	0x0098: 'ADD.MENU',
	0x0099: 'ADD.COMMAND',
	0x009A: 'ENABLE.COMMAND',
	0x009B: 'CHECK.COMMAND',
	0x009C: 'RENAME.COMMAND',
	0x009D: 'SHOW.BAR',
	0x009E: 'DELETE.MENU',
	0x009F: 'DELETE.COMMAND',
	0x00A0: 'GET.CHART.ITEM',
	0x00A1: 'DIALOG.BOX',
	0x00A2: 'CLEAN',
	0x00A3: 'MDETERM',
	0x00A4: 'MINVERSE',
	0x00A5: 'MMULT',
	0x00A6: 'FILES',
	0x00A7: 'IPMT',
	0x00A8: 'PPMT',
	0x00A9: 'COUNTA',
	0x00AA: 'CANCEL.KEY',
	0x00AB: 'FOR',
	0x00AC: 'WHILE',
	0x00AD: 'BREAK',
	0x00AE: 'NEXT',
	0x00AF: 'INITIATE',
	0x00B0: 'REQUEST',
	0x00B1: 'POKE',
	0x00B2: 'EXECUTE',
	0x00B3: 'TERMINATE',
	0x00B4: 'RESTART',
	0x00B5: 'HELP',
	0x00B6: 'GET.BAR',
	0x00B7: 'PRODUCT',
	0x00B8: 'FACT',
	0x00B9: 'GET.CELL',
	0x00BA: 'GET.WORKSPACE',
	0x00BB: 'GET.WINDOW',
	0x00BC: 'GET.DOCUMENT',
	0x00BD: 'DPRODUCT',
	0x00BE: 'ISNONTEXT',
	0x00BF: 'GET.NOTE',
	0x00C0: 'NOTE',
	0x00C1: 'STDEVP',
	0x00C2: 'VARP',
	0x00C3: 'DSTDEVP',
	0x00C4: 'DVARP',
	0x00C5: 'TRUNC',
	0x00C6: 'ISLOGICAL',
	0x00C7: 'DCOUNTA',
	0x00C8: 'DELETE.BAR',
	0x00C9: 'UNREGISTER',
	0x00CC: 'USDOLLAR',
	0x00CD: 'FINDB',
	0x00CE: 'SEARCHB',
	0x00CF: 'REPLACEB',
	0x00D0: 'LEFTB',
	0x00D1: 'RIGHTB',
	0x00D2: 'MIDB',
	0x00D3: 'LENB',
	0x00D4: 'ROUNDUP',
	0x00D5: 'ROUNDDOWN',
	0x00D6: 'ASC',
	0x00D7: 'DBCS',
	0x00D8: 'RANK',
	0x00DB: 'ADDRESS',
	0x00DC: 'DAYS360',
	0x00DD: 'TODAY',
	0x00DE: 'VDB',
	0x00DF: 'ELSE',
	0x00E0: 'ELSE.IF',
	0x00E1: 'END.IF',
	0x00E2: 'FOR.CELL',
	0x00E3: 'MEDIAN',
	0x00E4: 'SUMPRODUCT',
	0x00E5: 'SINH',
	0x00E6: 'COSH',
	0x00E7: 'TANH',
	0x00E8: 'ASINH',
	0x00E9: 'ACOSH',
	0x00EA: 'ATANH',
	0x00EB: 'DGET',
	0x00EC: 'CREATE.OBJECT',
	0x00ED: 'VOLATILE',
	0x00EE: 'LAST.ERROR',
	0x00EF: 'CUSTOM.UNDO',
	0x00F0: 'CUSTOM.REPEAT',
	0x00F1: 'FORMULA.CONVERT',
	0x00F2: 'GET.LINK.INFO',
	0x00F3: 'TEXT.BOX',
	0x00F4: 'INFO',
	0x00F5: 'GROUP',
	0x00F6: 'GET.OBJECT',
	0x00F7: 'DB',
	0x00F8: 'PAUSE',
	0x00FB: 'RESUME',
	0x00FC: 'FREQUENCY',
	0x00FD: 'ADD.TOOLBAR',
	0x00FE: 'DELETE.TOOLBAR',
	0x00FF: 'User',
	0x0100: 'RESET.TOOLBAR',
	0x0101: 'EVALUATE',
	0x0102: 'GET.TOOLBAR',
	0x0103: 'GET.TOOL',
	0x0104: 'SPELLING.CHECK',
	0x0105: 'ERROR.TYPE',
	0x0106: 'APP.TITLE',
	0x0107: 'WINDOW.TITLE',
	0x0108: 'SAVE.TOOLBAR',
	0x0109: 'ENABLE.TOOL',
	0x010A: 'PRESS.TOOL',
	0x010B: 'REGISTER.ID',
	0x010C: 'GET.WORKBOOK',
	0x010D: 'AVEDEV',
	0x010E: 'BETADIST',
	0x010F: 'GAMMALN',
	0x0110: 'BETAINV',
	0x0111: 'BINOMDIST',
	0x0112: 'CHIDIST',
	0x0113: 'CHIINV',
	0x0114: 'COMBIN',
	0x0115: 'CONFIDENCE',
	0x0116: 'CRITBINOM',
	0x0117: 'EVEN',
	0x0118: 'EXPONDIST',
	0x0119: 'FDIST',
	0x011A: 'FINV',
	0x011B: 'FISHER',
	0x011C: 'FISHERINV',
	0x011D: 'FLOOR',
	0x011E: 'GAMMADIST',
	0x011F: 'GAMMAINV',
	0x0120: 'CEILING',
	0x0121: 'HYPGEOMDIST',
	0x0122: 'LOGNORMDIST',
	0x0123: 'LOGINV',
	0x0124: 'NEGBINOMDIST',
	0x0125: 'NORMDIST',
	0x0126: 'NORMSDIST',
	0x0127: 'NORMINV',
	0x0128: 'NORMSINV',
	0x0129: 'STANDARDIZE',
	0x012A: 'ODD',
	0x012B: 'PERMUT',
	0x012C: 'POISSON',
	0x012D: 'TDIST',
	0x012E: 'WEIBULL',
	0x012F: 'SUMXMY2',
	0x0130: 'SUMX2MY2',
	0x0131: 'SUMX2PY2',
	0x0132: 'CHITEST',
	0x0133: 'CORREL',
	0x0134: 'COVAR',
	0x0135: 'FORECAST',
	0x0136: 'FTEST',
	0x0137: 'INTERCEPT',
	0x0138: 'PEARSON',
	0x0139: 'RSQ',
	0x013A: 'STEYX',
	0x013B: 'SLOPE',
	0x013C: 'TTEST',
	0x013D: 'PROB',
	0x013E: 'DEVSQ',
	0x013F: 'GEOMEAN',
	0x0140: 'HARMEAN',
	0x0141: 'SUMSQ',
	0x0142: 'KURT',
	0x0143: 'SKEW',
	0x0144: 'ZTEST',
	0x0145: 'LARGE',
	0x0146: 'SMALL',
	0x0147: 'QUARTILE',
	0x0148: 'PERCENTILE',
	0x0149: 'PERCENTRANK',
	0x014A: 'MODE',
	0x014B: 'TRIMMEAN',
	0x014C: 'TINV',
	0x014E: 'MOVIE.COMMAND',
	0x014F: 'GET.MOVIE',
	0x0150: 'CONCATENATE',
	0x0151: 'POWER',
	0x0152: 'PIVOT.ADD.DATA',
	0x0153: 'GET.PIVOT.TABLE',
	0x0154: 'GET.PIVOT.FIELD',
	0x0155: 'GET.PIVOT.ITEM',
	0x0156: 'RADIANS',
	0x0157: 'DEGREES',
	0x0158: 'SUBTOTAL',
	0x0159: 'SUMIF',
	0x015A: 'COUNTIF',
	0x015B: 'COUNTBLANK',
	0x015C: 'SCENARIO.GET',
	0x015D: 'OPTIONS.LISTS.GET',
	0x015E: 'ISPMT',
	0x015F: 'DATEDIF',
	0x0160: 'DATESTRING',
	0x0161: 'NUMBERSTRING',
	0x0162: 'ROMAN',
	0x0163: 'OPEN.DIALOG',
	0x0164: 'SAVE.DIALOG',
	0x0165: 'VIEW.GET',
	0x0166: 'GETPIVOTDATA',
	0x0167: 'HYPERLINK',
	0x0168: 'PHONETIC',
	0x0169: 'AVERAGEA',
	0x016A: 'MAXA',
	0x016B: 'MINA',
	0x016C: 'STDEVPA',
	0x016D: 'VARPA',
	0x016E: 'STDEVA',
	0x016F: 'VARA',
	0x0170: 'BAHTTEXT',
	0x0171: 'THAIDAYOFWEEK',
	0x0172: 'THAIDIGIT',
	0x0173: 'THAIMONTHOFYEAR',
	0x0174: 'THAINUMSOUND',
	0x0175: 'THAINUMSTRING',
	0x0176: 'THAISTRINGLENGTH',
	0x0177: 'ISTHAIDIGIT',
	0x0178: 'ROUNDBAHTDOWN',
	0x0179: 'ROUNDBAHTUP',
	0x017A: 'THAIYEAR',
	0x017B: 'RTD'
};
var FtabArgc = {
	0x0002: 1, /* ISNA */
	0x0003: 1, /* ISERROR */
	0x000F: 1, /* SIN */
	0x0010: 1, /* COS */
	0x0011: 1, /* TAN */
	0x0012: 1, /* ATAN */
	0x0014: 1, /* SQRT */
	0x0015: 1, /* EXP */
	0x0016: 1, /* LN */
	0x0017: 1, /* LOG10 */
	0x0018: 1, /* ABS */
	0x0019: 1, /* INT */
	0x001A: 1, /* SIGN */
	0x001B: 2, /* ROUND */
	0x001E: 2, /* REPT */
	0x001F: 3, /* MID */
	0x0020: 1, /* LEN */
	0x0021: 1, /* VALUE */
	0x0026: 1, /* NOT */
	0x0027: 2, /* MOD */
	0x0028: 3, /* DCOUNT */
	0x0029: 3, /* DSUM */
	0x002A: 3, /* DAVERAGE */
	0x002B: 3, /* DMIN */
	0x002C: 3, /* DMAX */
	0x002D: 3, /* DSTDEV */
	0x002F: 3, /* DVAR */
	0x0030: 2, /* TEXT */
	0x0035: 1, /* GOTO */
	0x003D: 3, /* MIRR */
	0x0041: 3, /* DATE */
	0x0042: 3, /* TIME */
	0x0043: 1, /* DAY */
	0x0044: 1, /* MONTH */
	0x0045: 1, /* YEAR */
	0x0047: 1, /* HOUR */
	0x0048: 1, /* MINUTE */
	0x0049: 1, /* SECOND */
	0x004B: 1, /* AREAS */
	0x004C: 1, /* ROWS */
	0x004D: 1, /* COLUMNS */
	0x004F: 2, /* ABSREF */
	0x0050: 2, /* RELREF */
	0x0053: 1, /* TRANSPOSE */
	0x0056: 1, /* TYPE */
	0x005A: 1, /* DEREF */
	0x0061: 2, /* ATAN2 */
	0x0062: 1, /* ASIN */
	0x0063: 1, /* ACOS */
	0x0069: 1, /* ISREF */
	0x006F: 1, /* CHAR */
	0x0070: 1, /* LOWER */
	0x0071: 1, /* UPPER */
	0x0072: 1, /* PROPER */
	0x0075: 2, /* EXACT */
	0x0076: 1, /* TRIM */
	0x0077: 4, /* REPLACE */
	0x0079: 1, /* CODE */
	0x007E: 1, /* ISERR */
	0x007F: 1, /* ISTEXT */
	0x0080: 1, /* ISNUMBER */
	0x0081: 1, /* ISBLANK */
	0x0082: 1, /* T */
	0x0083: 1, /* N */
	0x0085: 1, /* FCLOSE */
	0x0086: 1, /* FSIZE */
	0x0087: 1, /* FREADLN */
	0x0088: 2, /* FREAD */
	0x0089: 2, /* FWRITELN */
	0x008A: 2, /* FWRITE */
	0x008C: 1, /* DATEVALUE */
	0x008D: 1, /* TIMEVALUE */
	0x008E: 3, /* SLN */
	0x008F: 4, /* SYD */
	0x00A2: 1, /* CLEAN */
	0x00A3: 1, /* MDETERM */
	0x00A4: 1, /* MINVERSE */
	0x00A5: 2, /* MMULT */
	0x00AC: 1, /* WHILE */
	0x00AF: 2, /* INITIATE */
	0x00B0: 2, /* REQUEST */
	0x00B1: 3, /* POKE */
	0x00B2: 2, /* EXECUTE */
	0x00B3: 1, /* TERMINATE */
	0x00B8: 1, /* FACT */
	0x00BD: 3, /* DPRODUCT */
	0x00BE: 1, /* ISNONTEXT */
	0x00C3: 3, /* DSTDEVP */
	0x00C4: 3, /* DVARP */
	0x00C6: 1, /* ISLOGICAL */
	0x00C7: 3, /* DCOUNTA */
	0x00C9: 1, /* UNREGISTER */
	0x00CF: 4, /* REPLACEB */
	0x00D2: 3, /* MIDB */
	0x00D3: 1, /* LENB */
	0x00D4: 2, /* ROUNDUP */
	0x00D5: 2, /* ROUNDDOWN */
	0x00D6: 1, /* ASC */
	0x00D7: 1, /* DBCS */
	0x00E5: 1, /* SINH */
	0x00E6: 1, /* COSH */
	0x00E7: 1, /* TANH */
	0x00E8: 1, /* ASINH */
	0x00E9: 1, /* ACOSH */
	0x00EA: 1, /* ATANH */
	0x00EB: 3, /* DGET */
	0x00F4: 1, /* INFO */
	0x00FC: 2, /* FREQUENCY */
	0x0101: 1, /* EVALUATE */
	0x0105: 1, /* ERROR.TYPE */
	0x010F: 1, /* GAMMALN */
	0x0111: 4, /* BINOMDIST */
	0x0112: 2, /* CHIDIST */
	0x0113: 2, /* CHIINV */
	0x0114: 2, /* COMBIN */
	0x0115: 3, /* CONFIDENCE */
	0x0116: 3, /* CRITBINOM */
	0x0117: 1, /* EVEN */
	0x0118: 3, /* EXPONDIST */
	0x0119: 3, /* FDIST */
	0x011A: 3, /* FINV */
	0x011B: 1, /* FISHER */
	0x011C: 1, /* FISHERINV */
	0x011D: 2, /* FLOOR */
	0x011E: 4, /* GAMMADIST */
	0x011F: 3, /* GAMMAINV */
	0x0120: 2, /* CEILING */
	0x0121: 4, /* HYPGEOMDIST */
	0x0122: 3, /* LOGNORMDIST */
	0x0123: 3, /* LOGINV */
	0x0124: 3, /* NEGBINOMDIST */
	0x0125: 4, /* NORMDIST */
	0x0126: 1, /* NORMSDIST */
	0x0127: 3, /* NORMINV */
	0x0128: 1, /* NORMSINV */
	0x0129: 3, /* STANDARDIZE */
	0x012A: 1, /* ODD */
	0x012B: 2, /* PERMUT */
	0x012C: 3, /* POISSON */
	0x012D: 3, /* TDIST */
	0x012E: 4, /* WEIBULL */
	0x012F: 2, /* SUMXMY2 */
	0x0130: 2, /* SUMX2MY2 */
	0x0131: 2, /* SUMX2PY2 */
	0x0132: 2, /* CHITEST */
	0x0133: 2, /* CORREL */
	0x0134: 2, /* COVAR */
	0x0135: 3, /* FORECAST */
	0x0136: 2, /* FTEST */
	0x0137: 2, /* INTERCEPT */
	0x0138: 2, /* PEARSON */
	0x0139: 2, /* RSQ */
	0x013A: 2, /* STEYX */
	0x013B: 2, /* SLOPE */
	0x013C: 4, /* TTEST */
	0x0145: 2, /* LARGE */
	0x0146: 2, /* SMALL */
	0x0147: 2, /* QUARTILE */
	0x0148: 2, /* PERCENTILE */
	0x014B: 2, /* TRIMMEAN */
	0x014C: 2, /* TINV */
	0x0151: 2, /* POWER */
	0x0156: 1, /* RADIANS */
	0x0157: 1, /* DEGREES */
	0x015A: 2, /* COUNTIF */
	0x015B: 1, /* COUNTBLANK */
	0x015E: 4, /* ISPMT */
	0x015F: 3, /* DATEDIF */
	0x0160: 1, /* DATESTRING */
	0x0161: 2, /* NUMBERSTRING */
	0x0168: 1, /* PHONETIC */
	0x0170: 1, /* BAHTTEXT */
	0x0171: 1, /* THAIDAYOFWEEK */
	0x0172: 1, /* THAIDIGIT */
	0x0173: 1, /* THAIMONTHOFYEAR */
	0x0174: 1, /* THAINUMSOUND */
	0x0175: 1, /* THAINUMSTRING */
	0x0176: 1, /* THAISTRINGLENGTH */
	0x0177: 1, /* ISTHAIDIGIT */
	0x0178: 1, /* ROUNDBAHTDOWN */
	0x0179: 1, /* ROUNDBAHTUP */
	0x017A: 1, /* THAIYEAR */
	0xFFFF: 0
};
/* [MS-XLSX] 2.2.3 Functions */
var XLSXFutureFunctions = {
	"_xlfn.ACOT": "ACOT",
	"_xlfn.ACOTH": "ACOTH",
	"_xlfn.AGGREGATE": "AGGREGATE",
	"_xlfn.ARABIC": "ARABIC",
	"_xlfn.AVERAGEIF": "AVERAGEIF",
	"_xlfn.AVERAGEIFS": "AVERAGEIFS",
	"_xlfn.BASE": "BASE",
	"_xlfn.BETA.DIST": "BETA.DIST",
	"_xlfn.BETA.INV": "BETA.INV",
	"_xlfn.BINOM.DIST": "BINOM.DIST",
	"_xlfn.BINOM.DIST.RANGE": "BINOM.DIST.RANGE",
	"_xlfn.BINOM.INV": "BINOM.INV",
	"_xlfn.BITAND": "BITAND",
	"_xlfn.BITLSHIFT": "BITLSHIFT",
	"_xlfn.BITOR": "BITOR",
	"_xlfn.BITRSHIFT": "BITRSHIFT",
	"_xlfn.BITXOR": "BITXOR",
	"_xlfn.CEILING.MATH": "CEILING.MATH",
	"_xlfn.CEILING.PRECISE": "CEILING.PRECISE",
	"_xlfn.CHISQ.DIST": "CHISQ.DIST",
	"_xlfn.CHISQ.DIST.RT": "CHISQ.DIST.RT",
	"_xlfn.CHISQ.INV": "CHISQ.INV",
	"_xlfn.CHISQ.INV.RT": "CHISQ.INV.RT",
	"_xlfn.CHISQ.TEST": "CHISQ.TEST",
	"_xlfn.COMBINA": "COMBINA",
	"_xlfn.CONFIDENCE.NORM": "CONFIDENCE.NORM",
	"_xlfn.CONFIDENCE.T": "CONFIDENCE.T",
	"_xlfn.COT": "COT",
	"_xlfn.COTH": "COTH",
	"_xlfn.COUNTIFS": "COUNTIFS",
	"_xlfn.COVARIANCE.P": "COVARIANCE.P",
	"_xlfn.COVARIANCE.S": "COVARIANCE.S",
	"_xlfn.CSC": "CSC",
	"_xlfn.CSCH": "CSCH",
	"_xlfn.DAYS": "DAYS",
	"_xlfn.DECIMAL": "DECIMAL",
	"_xlfn.ECMA.CEILING": "ECMA.CEILING",
	"_xlfn.ERF.PRECISE": "ERF.PRECISE",
	"_xlfn.ERFC.PRECISE": "ERFC.PRECISE",
	"_xlfn.EXPON.DIST": "EXPON.DIST",
	"_xlfn.F.DIST": "F.DIST",
	"_xlfn.F.DIST.RT": "F.DIST.RT",
	"_xlfn.F.INV": "F.INV",
	"_xlfn.F.INV.RT": "F.INV.RT",
	"_xlfn.F.TEST": "F.TEST",
	"_xlfn.FILTERXML": "FILTERXML",
	"_xlfn.FLOOR.MATH": "FLOOR.MATH",
	"_xlfn.FLOOR.PRECISE": "FLOOR.PRECISE",
	"_xlfn.FORMULATEXT": "FORMULATEXT",
	"_xlfn.GAMMA": "GAMMA",
	"_xlfn.GAMMA.DIST": "GAMMA.DIST",
	"_xlfn.GAMMA.INV": "GAMMA.INV",
	"_xlfn.GAMMALN.PRECISE": "GAMMALN.PRECISE",
	"_xlfn.GAUSS": "GAUSS",
	"_xlfn.HYPGEOM.DIST": "HYPGEOM.DIST",
	"_xlfn.IFNA": "IFNA",
	"_xlfn.IFERROR": "IFERROR",
	"_xlfn.IMCOSH": "IMCOSH",
	"_xlfn.IMCOT": "IMCOT",
	"_xlfn.IMCSC": "IMCSC",
	"_xlfn.IMCSCH": "IMCSCH",
	"_xlfn.IMSEC": "IMSEC",
	"_xlfn.IMSECH": "IMSECH",
	"_xlfn.IMSINH": "IMSINH",
	"_xlfn.IMTAN": "IMTAN",
	"_xlfn.ISFORMULA": "ISFORMULA",
	"_xlfn.ISO.CEILING": "ISO.CEILING",
	"_xlfn.ISOWEEKNUM": "ISOWEEKNUM",
	"_xlfn.LOGNORM.DIST": "LOGNORM.DIST",
	"_xlfn.LOGNORM.INV": "LOGNORM.INV",
	"_xlfn.MODE.MULT": "MODE.MULT",
	"_xlfn.MODE.SNGL": "MODE.SNGL",
	"_xlfn.MUNIT": "MUNIT",
	"_xlfn.NEGBINOM.DIST": "NEGBINOM.DIST",
	"_xlfn.NETWORKDAYS.INTL": "NETWORKDAYS.INTL",
	"_xlfn.NIGBINOM": "NIGBINOM",
	"_xlfn.NORM.DIST": "NORM.DIST",
	"_xlfn.NORM.INV": "NORM.INV",
	"_xlfn.NORM.S.DIST": "NORM.S.DIST",
	"_xlfn.NORM.S.INV": "NORM.S.INV",
	"_xlfn.NUMBERVALUE": "NUMBERVALUE",
	"_xlfn.PDURATION": "PDURATION",
	"_xlfn.PERCENTILE.EXC": "PERCENTILE.EXC",
	"_xlfn.PERCENTILE.INC": "PERCENTILE.INC",
	"_xlfn.PERCENTRANK.EXC": "PERCENTRANK.EXC",
	"_xlfn.PERCENTRANK.INC": "PERCENTRANK.INC",
	"_xlfn.PERMUTATIONA": "PERMUTATIONA",
	"_xlfn.PHI": "PHI",
	"_xlfn.POISSON.DIST": "POISSON.DIST",
	"_xlfn.QUARTILE.EXC": "QUARTILE.EXC",
	"_xlfn.QUARTILE.INC": "QUARTILE.INC",
	"_xlfn.QUERYSTRING": "QUERYSTRING",
	"_xlfn.RANK.AVG": "RANK.AVG",
	"_xlfn.RANK.EQ": "RANK.EQ",
	"_xlfn.RRI": "RRI",
	"_xlfn.SEC": "SEC",
	"_xlfn.SECH": "SECH",
	"_xlfn.SHEET": "SHEET",
	"_xlfn.SHEETS": "SHEETS",
	"_xlfn.SKEW.P": "SKEW.P",
	"_xlfn.STDEV.P": "STDEV.P",
	"_xlfn.STDEV.S": "STDEV.S",
	"_xlfn.SUMIFS": "SUMIFS",
	"_xlfn.T.DIST": "T.DIST",
	"_xlfn.T.DIST.2T": "T.DIST.2T",
	"_xlfn.T.DIST.RT": "T.DIST.RT",
	"_xlfn.T.INV": "T.INV",
	"_xlfn.T.INV.2T": "T.INV.2T",
	"_xlfn.T.TEST": "T.TEST",
	"_xlfn.UNICHAR": "UNICHAR",
	"_xlfn.UNICODE": "UNICODE",
	"_xlfn.VAR.P": "VAR.P",
	"_xlfn.VAR.S": "VAR.S",
	"_xlfn.WEBSERVICE": "WEBSERVICE",
	"_xlfn.WEIBULL.DIST": "WEIBULL.DIST",
	"_xlfn.WORKDAY.INTL": "WORKDAY.INTL",
	"_xlfn.XOR": "XOR",
	"_xlfn.Z.TEST": "Z.TEST"
};
var RecordEnum = {
	0x0006: { n:"Formula", f:parse_Formula },
	0x000a: { n:'EOF', f:parse_EOF },
	0x000c: { n:"CalcCount", f:parse_CalcCount },
	0x000d: { n:"CalcMode", f:parse_CalcMode },
	0x000e: { n:"CalcPrecision", f:parse_CalcPrecision },
	0x000f: { n:"CalcRefMode", f:parse_CalcRefMode },
	0x0010: { n:"CalcDelta", f:parse_CalcDelta },
	0x0011: { n:"CalcIter", f:parse_CalcIter },
	0x0012: { n:"Protect", f:parse_Protect },
	0x0013: { n:"Password", f:parse_Password },
	0x0014: { n:"Header", f:parse_Header },
	0x0015: { n:"Footer", f:parse_Footer },
	0x0017: { n:"ExternSheet", f:parse_ExternSheet },
	0x0018: { n:"Lbl", f:parse_Lbl },
	0x0019: { n:"WinProtect", f:parse_WinProtect },
	0x001a: { n:"VerticalPageBreaks", f:parse_VerticalPageBreaks },
	0x001b: { n:"HorizontalPageBreaks", f:parse_HorizontalPageBreaks },
	0x001c: { n:"Note", f:parse_Note },
	0x001d: { n:"Selection", f:parse_Selection },
	0x0022: { n:"Date1904", f:parse_Date1904 },
	0x0023: { n:"ExternName", f:parse_ExternName },
	0x0026: { n:"LeftMargin", f:parse_LeftMargin },
	0x0027: { n:"RightMargin", f:parse_RightMargin },
	0x0028: { n:"TopMargin", f:parse_TopMargin },
	0x0029: { n:"BottomMargin", f:parse_BottomMargin },
	0x002a: { n:"PrintRowCol", f:parse_PrintRowCol },
	0x002b: { n:"PrintGrid", f:parse_PrintGrid },
	0x002f: { n:"FilePass", f:parse_FilePass },
	0x0031: { n:"Font", f:parse_Font },
	0x0033: { n:"PrintSize", f:parse_PrintSize },
	0x003c: { n:"Continue", f:parse_Continue },
	0x003d: { n:"Window1", f:parse_Window1 },
	0x0040: { n:"Backup", f:parse_Backup },
	0x0041: { n:"Pane", f:parse_Pane },
	0x0042: { n:'CodePage', f:parse_CodePage },
	0x004d: { n:"Pls", f:parse_Pls },
	0x0050: { n:"DCon", f:parse_DCon },
	0x0051: { n:"DConRef", f:parse_DConRef },
	0x0052: { n:"DConName", f:parse_DConName },
	0x0055: { n:"DefColWidth", f:parse_DefColWidth },
	0x0059: { n:"XCT", f:parse_XCT },
	0x005a: { n:"CRN", f:parse_CRN },
	0x005b: { n:"FileSharing", f:parse_FileSharing },
	0x005c: { n:'WriteAccess', f:parse_WriteAccess },
	0x005d: { n:"Obj", f:parse_Obj },
	0x005e: { n:"Uncalced", f:parse_Uncalced },
	0x005f: { n:"CalcSaveRecalc", f:parse_CalcSaveRecalc },
	0x0060: { n:"Template", f:parse_Template },
	0x0061: { n:"Intl", f:parse_Intl },
	0x0063: { n:"ObjProtect", f:parse_ObjProtect },
	0x007d: { n:"ColInfo", f:parse_ColInfo },
	0x0080: { n:"Guts", f:parse_Guts },
	0x0081: { n:"WsBool", f:parse_WsBool },
	0x0082: { n:"GridSet", f:parse_GridSet },
	0x0083: { n:"HCenter", f:parse_HCenter },
	0x0084: { n:"VCenter", f:parse_VCenter },
	0x0085: { n:'BoundSheet8', f:parse_BoundSheet8 },
	0x0086: { n:"WriteProtect", f:parse_WriteProtect },
	0x008c: { n:"Country", f:parse_Country },
	0x008d: { n:"HideObj", f:parse_HideObj },
	0x0090: { n:"Sort", f:parse_Sort },
	0x0092: { n:"Palette", f:parse_Palette },
	0x0097: { n:"Sync", f:parse_Sync },
	0x0098: { n:"LPr", f:parse_LPr },
	0x0099: { n:"DxGCol", f:parse_DxGCol },
	0x009a: { n:"FnGroupName", f:parse_FnGroupName },
	0x009b: { n:"FilterMode", f:parse_FilterMode },
	0x009c: { n:"BuiltInFnGroupCount", f:parse_BuiltInFnGroupCount },
	0x009d: { n:"AutoFilterInfo", f:parse_AutoFilterInfo },
	0x009e: { n:"AutoFilter", f:parse_AutoFilter },
	0x00a0: { n:"Scl", f:parse_Scl },
	0x00a1: { n:"Setup", f:parse_Setup },
	0x00ae: { n:"ScenMan", f:parse_ScenMan },
	0x00af: { n:"SCENARIO", f:parse_SCENARIO },
	0x00b0: { n:"SxView", f:parse_SxView },
	0x00b1: { n:"Sxvd", f:parse_Sxvd },
	0x00b2: { n:"SXVI", f:parse_SXVI },
	0x00b4: { n:"SxIvd", f:parse_SxIvd },
	0x00b5: { n:"SXLI", f:parse_SXLI },
	0x00b6: { n:"SXPI", f:parse_SXPI },
	0x00b8: { n:"DocRoute", f:parse_DocRoute },
	0x00b9: { n:"RecipName", f:parse_RecipName },
	0x00bd: { n:"MulRk", f:parse_MulRk },
	0x00be: { n:"MulBlank", f:parse_MulBlank },
	0x00c1: { n:'Mms', f:parse_Mms },
	0x00c5: { n:"SXDI", f:parse_SXDI },
	0x00c6: { n:"SXDB", f:parse_SXDB },
	0x00c7: { n:"SXFDB", f:parse_SXFDB },
	0x00c8: { n:"SXDBB", f:parse_SXDBB },
	0x00c9: { n:"SXNum", f:parse_SXNum },
	0x00ca: { n:"SxBool", f:parse_SxBool },
	0x00cb: { n:"SxErr", f:parse_SxErr },
	0x00cc: { n:"SXInt", f:parse_SXInt },
	0x00cd: { n:"SXString", f:parse_SXString },
	0x00ce: { n:"SXDtr", f:parse_SXDtr },
	0x00cf: { n:"SxNil", f:parse_SxNil },
	0x00d0: { n:"SXTbl", f:parse_SXTbl },
	0x00d1: { n:"SXTBRGIITM", f:parse_SXTBRGIITM },
	0x00d2: { n:"SxTbpg", f:parse_SxTbpg },
	0x00d3: { n:"ObProj", f:parse_ObProj },
	0x00d5: { n:"SXStreamID", f:parse_SXStreamID },
	0x00d7: { n:"DBCell", f:parse_DBCell },
	0x00d8: { n:"SXRng", f:parse_SXRng },
	0x00d9: { n:"SxIsxoper", f:parse_SxIsxoper },
	0x00da: { n:"BookBool", f:parse_BookBool },
	0x00dc: { n:"DbOrParamQry", f:parse_DbOrParamQry },
	0x00dd: { n:"ScenarioProtect", f:parse_ScenarioProtect },
	0x00de: { n:"OleObjectSize", f:parse_OleObjectSize },
	0x00e0: { n:"XF", f:parse_XF },
	0x00e1: { n:'InterfaceHdr', f:parse_InterfaceHdr },
	0x00e2: { n:'InterfaceEnd', f:parse_InterfaceEnd },
	0x00e3: { n:"SXVS", f:parse_SXVS },
	0x00e5: { n:"MergeCells", f:parse_MergeCells },
	0x00e9: { n:"BkHim", f:parse_BkHim },
	0x00eb: { n:"MsoDrawingGroup", f:parse_MsoDrawingGroup },
	0x00ec: { n:"MsoDrawing", f:parse_MsoDrawing },
	0x00ed: { n:"MsoDrawingSelection", f:parse_MsoDrawingSelection },
	0x00ef: { n:"PhoneticInfo", f:parse_PhoneticInfo },
	0x00f0: { n:"SxRule", f:parse_SxRule },
	0x00f1: { n:"SXEx", f:parse_SXEx },
	0x00f2: { n:"SxFilt", f:parse_SxFilt },
	0x00f4: { n:"SxDXF", f:parse_SxDXF },
	0x00f5: { n:"SxItm", f:parse_SxItm },
	0x00f6: { n:"SxName", f:parse_SxName },
	0x00f7: { n:"SxSelect", f:parse_SxSelect },
	0x00f8: { n:"SXPair", f:parse_SXPair },
	0x00f9: { n:"SxFmla", f:parse_SxFmla },
	0x00fb: { n:"SxFormat", f:parse_SxFormat },
	0x00fc: { n:"SST", f:parse_SST },
	0x00fd: { n:"LabelSst", f:parse_LabelSst },
	0x00ff: { n:"ExtSST", f:parse_ExtSST },
	0x0100: { n:"SXVDEx", f:parse_SXVDEx },
	0x0103: { n:"SXFormula", f:parse_SXFormula },
	0x0122: { n:"SXDBEx", f:parse_SXDBEx },
	0x0137: { n:"RRDInsDel", f:parse_RRDInsDel },
	0x0138: { n:"RRDHead", f:parse_RRDHead },
	0x013b: { n:"RRDChgCell", f:parse_RRDChgCell },
	0x013d: { n:"RRTabId", f:parse_RRTabId },
	0x013e: { n:"RRDRenSheet", f:parse_RRDRenSheet },
	0x013f: { n:"RRSort", f:parse_RRSort },
	0x0140: { n:"RRDMove", f:parse_RRDMove },
	0x014a: { n:"RRFormat", f:parse_RRFormat },
	0x014b: { n:"RRAutoFmt", f:parse_RRAutoFmt },
	0x014d: { n:"RRInsertSh", f:parse_RRInsertSh },
	0x014e: { n:"RRDMoveBegin", f:parse_RRDMoveBegin },
	0x014f: { n:"RRDMoveEnd", f:parse_RRDMoveEnd },
	0x0150: { n:"RRDInsDelBegin", f:parse_RRDInsDelBegin },
	0x0151: { n:"RRDInsDelEnd", f:parse_RRDInsDelEnd },
	0x0152: { n:"RRDConflict", f:parse_RRDConflict },
	0x0153: { n:"RRDDefName", f:parse_RRDDefName },
	0x0154: { n:"RRDRstEtxp", f:parse_RRDRstEtxp },
	0x015f: { n:"LRng", f:parse_LRng },
	0x0160: { n:"UsesELFs", f:parse_UsesELFs },
	0x0161: { n:"DSF", f:parse_DSF },
	0x0191: { n:"CUsr", f:parse_CUsr },
	0x0192: { n:"CbUsr", f:parse_CbUsr },
	0x0193: { n:"UsrInfo", f:parse_UsrInfo },
	0x0194: { n:"UsrExcl", f:parse_UsrExcl },
	0x0195: { n:"FileLock", f:parse_FileLock },
	0x0196: { n:"RRDInfo", f:parse_RRDInfo },
	0x0197: { n:"BCUsrs", f:parse_BCUsrs },
	0x0198: { n:"UsrChk", f:parse_UsrChk },
	0x01a9: { n:"UserBView", f:parse_UserBView },
	0x01aa: { n:"UserSViewBegin", f:parse_UserSViewBegin },
	0x01ab: { n:"UserSViewEnd", f:parse_UserSViewEnd },
	0x01ac: { n:"RRDUserView", f:parse_RRDUserView },
	0x01ad: { n:"Qsi", f:parse_Qsi },
	0x01ae: { n:"SupBook", f:parse_SupBook },
	0x01af: { n:"Prot4Rev", f:parse_Prot4Rev },
	0x01b0: { n:"CondFmt", f:parse_CondFmt },
	0x01b1: { n:"CF", f:parse_CF },
	0x01b2: { n:"DVal", f:parse_DVal },
	0x01b5: { n:"DConBin", f:parse_DConBin },
	0x01b6: { n:"TxO", f:parse_TxO },
	0x01b7: { n:"RefreshAll", f:parse_RefreshAll },
	0x01b8: { n:"HLink", f:parse_HLink },
	0x01b9: { n:"Lel", f:parse_Lel },
	0x01ba: { n:"CodeName", f:parse_CodeName },
	0x01bb: { n:"SXFDBType", f:parse_SXFDBType },
	0x01bc: { n:"Prot4RevPass", f:parse_Prot4RevPass },
	0x01bd: { n:"ObNoMacros", f:parse_ObNoMacros },
	0x01be: { n:"Dv", f:parse_Dv },
	0x01c0: { n:"Excel9File", f:parse_Excel9File },
	0x01c1: { n:"RecalcId", f:parse_RecalcId, r:2},
	0x01c2: { n:"EntExU2", f:parse_EntExU2 },
	0x0200: { n:"Dimensions", f:parse_Dimensions },
	0x0201: { n:"Blank", f:parse_Blank },
	0x0203: { n:"Number", f:parse_Number },
	0x0204: { n:"Label", f:parse_Label },
	0x0205: { n:"BoolErr", f:parse_BoolErr },
	0x0207: { n:"String", f:parse_String },
	0x0208: { n:'Row', f:parse_Row },
	0x020b: { n:"Index", f:parse_Index },
	0x0221: { n:"Array", f:parse_Array },
	0x0225: { n:"DefaultRowHeight", f:parse_DefaultRowHeight },
	0x0236: { n:"Table", f:parse_Table },
	0x023e: { n:"Window2", f:parse_Window2 },
	0x027e: { n:"RK", f:parse_RK },
	0x0293: { n:"Style", f:parse_Style },
	0x0418: { n:"BigName", f:parse_BigName },
	0x041e: { n:"Format", f:parse_Format },
	0x043c: { n:"ContinueBigName", f:parse_ContinueBigName },
	0x04bc: { n:"ShrFmla", f:parse_ShrFmla },
	0x0800: { n:"HLinkTooltip", f:parse_HLinkTooltip },
	0x0801: { n:"WebPub", f:parse_WebPub },
	0x0802: { n:"QsiSXTag", f:parse_QsiSXTag },
	0x0803: { n:"DBQueryExt", f:parse_DBQueryExt },
	0x0804: { n:"ExtString", f:parse_ExtString },
	0x0805: { n:"TxtQry", f:parse_TxtQry },
	0x0806: { n:"Qsir", f:parse_Qsir },
	0x0807: { n:"Qsif", f:parse_Qsif },
	0x0808: { n:"RRDTQSIF", f:parse_RRDTQSIF },
	0x0809: { n:'BOF', f:parse_BOF },
	0x080a: { n:"OleDbConn", f:parse_OleDbConn },
	0x080b: { n:"WOpt", f:parse_WOpt },
	0x080c: { n:"SXViewEx", f:parse_SXViewEx },
	0x080d: { n:"SXTH", f:parse_SXTH },
	0x080e: { n:"SXPIEx", f:parse_SXPIEx },
	0x080f: { n:"SXVDTEx", f:parse_SXVDTEx },
	0x0810: { n:"SXViewEx9", f:parse_SXViewEx9 },
	0x0812: { n:"ContinueFrt", f:parse_ContinueFrt },
	0x0813: { n:"RealTimeData", f:parse_RealTimeData },
	0x0850: { n:"ChartFrtInfo", f:parse_ChartFrtInfo },
	0x0851: { n:"FrtWrapper", f:parse_FrtWrapper },
	0x0852: { n:"StartBlock", f:parse_StartBlock },
	0x0853: { n:"EndBlock", f:parse_EndBlock },
	0x0854: { n:"StartObject", f:parse_StartObject },
	0x0855: { n:"EndObject", f:parse_EndObject },
	0x0856: { n:"CatLab", f:parse_CatLab },
	0x0857: { n:"YMult", f:parse_YMult },
	0x0858: { n:"SXViewLink", f:parse_SXViewLink },
	0x0859: { n:"PivotChartBits", f:parse_PivotChartBits },
	0x085a: { n:"FrtFontList", f:parse_FrtFontList },
	0x0862: { n:"SheetExt", f:parse_SheetExt },
	0x0863: { n:"BookExt", f:parse_BookExt, r:12},
	0x0864: { n:"SXAddl", f:parse_SXAddl },
	0x0865: { n:"CrErr", f:parse_CrErr },
	0x0866: { n:"HFPicture", f:parse_HFPicture },
	0x0867: { n:'FeatHdr', f:parse_FeatHdr },
	0x0868: { n:"Feat", f:parse_Feat },
	0x086a: { n:"DataLabExt", f:parse_DataLabExt },
	0x086b: { n:"DataLabExtContents", f:parse_DataLabExtContents },
	0x086c: { n:"CellWatch", f:parse_CellWatch },
	0x0871: { n:"FeatHdr11", f:parse_FeatHdr11 },
	0x0872: { n:"Feature11", f:parse_Feature11 },
	0x0874: { n:"DropDownObjIds", f:parse_DropDownObjIds },
	0x0875: { n:"ContinueFrt11", f:parse_ContinueFrt11 },
	0x0876: { n:"DConn", f:parse_DConn },
	0x0877: { n:"List12", f:parse_List12 },
	0x0878: { n:"Feature12", f:parse_Feature12 },
	0x0879: { n:"CondFmt12", f:parse_CondFmt12 },
	0x087a: { n:"CF12", f:parse_CF12 },
	0x087b: { n:"CFEx", f:parse_CFEx },
	0x087c: { n:"XFCRC", f:parse_XFCRC },
	0x087d: { n:"XFExt", f:parse_XFExt },
	0x087e: { n:"AutoFilter12", f:parse_AutoFilter12 },
	0x087f: { n:"ContinueFrt12", f:parse_ContinueFrt12 },
	0x0884: { n:"MDTInfo", f:parse_MDTInfo },
	0x0885: { n:"MDXStr", f:parse_MDXStr },
	0x0886: { n:"MDXTuple", f:parse_MDXTuple },
	0x0887: { n:"MDXSet", f:parse_MDXSet },
	0x0888: { n:"MDXProp", f:parse_MDXProp },
	0x0889: { n:"MDXKPI", f:parse_MDXKPI },
	0x088a: { n:"MDB", f:parse_MDB },
	0x088b: { n:"PLV", f:parse_PLV },
	0x088c: { n:"Compat12", f:parse_Compat12, r:12 },
	0x088d: { n:"DXF", f:parse_DXF },
	0x088e: { n:"TableStyles", f:parse_TableStyles, r:12 },
	0x088f: { n:"TableStyle", f:parse_TableStyle },
	0x0890: { n:"TableStyleElement", f:parse_TableStyleElement },
	0x0892: { n:"StyleExt", f:parse_StyleExt },
	0x0893: { n:"NamePublish", f:parse_NamePublish },
	0x0894: { n:"NameCmt", f:parse_NameCmt },
	0x0895: { n:"SortData", f:parse_SortData },
	0x0896: { n:"Theme", f:parse_Theme },
	0x0897: { n:"GUIDTypeLib", f:parse_GUIDTypeLib },
	0x0898: { n:"FnGrp12", f:parse_FnGrp12 },
	0x0899: { n:"NameFnGrp12", f:parse_NameFnGrp12 },
	0x089a: { n:"MTRSettings", f:parse_MTRSettings, r:12 },
	0x089b: { n:"CompressPictures", f:parse_CompressPictures },
	0x089c: { n:"HeaderFooter", f:parse_HeaderFooter },
	0x089d: { n:"CrtLayout12", f:parse_CrtLayout12 },
	0x089e: { n:"CrtMlFrt", f:parse_CrtMlFrt },
	0x089f: { n:"CrtMlFrtContinue", f:parse_CrtMlFrtContinue },
	0x08a3: { n:"ForceFullCalculation", f:parse_ForceFullCalculation },
	0x08a4: { n:"ShapePropsStream", f:parse_ShapePropsStream },
	0x08a5: { n:"TextPropsStream", f:parse_TextPropsStream },
	0x08a6: { n:"RichTextStream", f:parse_RichTextStream },
	0x08a7: { n:"CrtLayout12A", f:parse_CrtLayout12A },
	0x1001: { n:"Units", f:parse_Units },
	0x1002: { n:"Chart", f:parse_Chart },
	0x1003: { n:"Series", f:parse_Series },
	0x1006: { n:"DataFormat", f:parse_DataFormat },
	0x1007: { n:"LineFormat", f:parse_LineFormat },
	0x1009: { n:"MarkerFormat", f:parse_MarkerFormat },
	0x100a: { n:"AreaFormat", f:parse_AreaFormat },
	0x100b: { n:"PieFormat", f:parse_PieFormat },
	0x100c: { n:"AttachedLabel", f:parse_AttachedLabel },
	0x100d: { n:"SeriesText", f:parse_SeriesText },
	0x1014: { n:"ChartFormat", f:parse_ChartFormat },
	0x1015: { n:"Legend", f:parse_Legend },
	0x1016: { n:"SeriesList", f:parse_SeriesList },
	0x1017: { n:"Bar", f:parse_Bar },
	0x1018: { n:"Line", f:parse_Line },
	0x1019: { n:"Pie", f:parse_Pie },
	0x101a: { n:"Area", f:parse_Area },
	0x101b: { n:"Scatter", f:parse_Scatter },
	0x101c: { n:"CrtLine", f:parse_CrtLine },
	0x101d: { n:"Axis", f:parse_Axis },
	0x101e: { n:"Tick", f:parse_Tick },
	0x101f: { n:"ValueRange", f:parse_ValueRange },
	0x1020: { n:"CatSerRange", f:parse_CatSerRange },
	0x1021: { n:"AxisLine", f:parse_AxisLine },
	0x1022: { n:"CrtLink", f:parse_CrtLink },
	0x1024: { n:"DefaultText", f:parse_DefaultText },
	0x1025: { n:"Text", f:parse_Text },
	0x1026: { n:"FontX", f:parse_FontX },
	0x1027: { n:"ObjectLink", f:parse_ObjectLink },
	0x1032: { n:"Frame", f:parse_Frame },
	0x1033: { n:"Begin", f:parse_Begin },
	0x1034: { n:"End", f:parse_End },
	0x1035: { n:"PlotArea", f:parse_PlotArea },
	0x103a: { n:"Chart3d", f:parse_Chart3d },
	0x103c: { n:"PicF", f:parse_PicF },
	0x103d: { n:"DropBar", f:parse_DropBar },
	0x103e: { n:"Radar", f:parse_Radar },
	0x103f: { n:"Surf", f:parse_Surf },
	0x1040: { n:"RadarArea", f:parse_RadarArea },
	0x1041: { n:"AxisParent", f:parse_AxisParent },
	0x1043: { n:"LegendException", f:parse_LegendException },
	0x1044: { n:"ShtProps", f:parse_ShtProps },
	0x1045: { n:"SerToCrt", f:parse_SerToCrt },
	0x1046: { n:"AxesUsed", f:parse_AxesUsed },
	0x1048: { n:"SBaseRef", f:parse_SBaseRef },
	0x104a: { n:"SerParent", f:parse_SerParent },
	0x104b: { n:"SerAuxTrend", f:parse_SerAuxTrend },
	0x104e: { n:"IFmtRecord", f:parse_IFmtRecord },
	0x104f: { n:"Pos", f:parse_Pos },
	0x1050: { n:"AlRuns", f:parse_AlRuns },
	0x1051: { n:"BRAI", f:parse_BRAI },
	0x105b: { n:"SerAuxErrBar", f:parse_SerAuxErrBar },
	0x105c: { n:"ClrtClient", f:parse_ClrtClient },
	0x105d: { n:"SerFmt", f:parse_SerFmt },
	0x105f: { n:"Chart3DBarShape", f:parse_Chart3DBarShape },
	0x1060: { n:"Fbi", f:parse_Fbi },
	0x1061: { n:"BopPop", f:parse_BopPop },
	0x1062: { n:"AxcExt", f:parse_AxcExt },
	0x1063: { n:"Dat", f:parse_Dat },
	0x1064: { n:"PlotGrowth", f:parse_PlotGrowth },
	0x1065: { n:"SIIndex", f:parse_SIIndex },
	0x1066: { n:"GelFrame", f:parse_GelFrame },
	0x1067: { n:"BopPopCustom", f:parse_BopPopCustom },
	0x1068: { n:"Fbi2", f:parse_Fbi2 },

	/* These are specified in an older version of the spec */
	0x0016: { n:"ExternCount", f:parsenoop },
	0x007e: { n:"RK", f:parsenoop }, /* Not necessarily same as 0x027e */
	0x007f: { n:"ImData", f:parsenoop },
	0x0087: { n:"Addin", f:parsenoop },
	0x0088: { n:"Edg", f:parsenoop },
	0x0089: { n:"Pub", f:parsenoop },
	0x0091: { n:"Sub", f:parsenoop },
	0x0094: { n:"LHRecord", f:parsenoop },
	0x0095: { n:"LHNGraph", f:parsenoop },
	0x0096: { n:"Sound", f:parsenoop },
	0x00a9: { n:"CoordList", f:parsenoop },
	0x00ab: { n:"GCW", f:parsenoop },
	0x00bc: { n:"ShrFmla", f:parsenoop }, /* Not necessarily same as 0x04bc */
	0x00c2: { n:"AddMenu", f:parsenoop },
	0x00c3: { n:"DelMenu", f:parsenoop },
	0x00d6: { n:"RString", f:parsenoop },
	0x00df: { n:"UDDesc", f:parsenoop },
	0x00ea: { n:"TabIdConf", f:parsenoop },
	0x0162: { n:"XL5Modify", f:parsenoop },
	0x01a5: { n:"FileSharing2", f:parsenoop },
	0x0218: { n:"Name", f:parsenoop },
	0x0223: { n:"ExternName", f:parse_ExternName },
	0x0231: { n:"Font", f:parsenoop },
	0x0406: { n:"Formula", f:parse_Formula },
	0x086d: { n:"FeatInfo", f:parsenoop },
	0x0873: { n:"FeatInfo11", f:parsenoop },
	0x0881: { n:"SXAddl12", f:parsenoop },
	0x08c0: { n:"AutoWebPub", f:parsenoop },
	0x08c1: { n:"ListObj", f:parsenoop },
	0x08c2: { n:"ListField", f:parsenoop },
	0x08c3: { n:"ListDV", f:parsenoop },
	0x08c4: { n:"ListCondFmt", f:parsenoop },
	0x08c5: { n:"ListCF", f:parsenoop },
	0x08c6: { n:"FMQry", f:parsenoop },
	0x08c7: { n:"FMSQry", f:parsenoop },
	0x08c8: { n:"PLV", f:parsenoop }, /* supposedly PLV for Excel 11 */
	0x08c9: { n:"LnExt", f:parsenoop },
	0x08ca: { n:"MkrExt", f:parsenoop },
	0x08cb: { n:"CrtCoopt", f:parsenoop },

	0x0000: {}
};

/* [MS-OLEDS] 2.3.8 CompObjStream */
function parse_compobj(obj) {
	var v = {};
	var o = obj.content;

	/* [MS-OLEDS] 2.3.7 CompObjHeader -- All fields MUST be ignored */
	var l = 28, m;
	m = o.lpstr(l);
	l += 4 + o.readUInt32LE(l);
	v.UserType = m;

	/* [MS-OLEDS] 2.3.1 ClipboardFormatOrAnsiString */
	m = o.readUInt32LE(l); l+= 4;
	switch(m) {
		case 0x00000000: break;
		case 0xffffffff: case 0xfffffffe: l+=4; break;
		default:
			if(m > 0x190) throw new Error("Unsupported Clipboard: " + m.toString(16));
			l += m;
	}

	m = o.lpstr(l); l += m.length === 0 ? 0 : 5 + m.length; v.Reserved1 = m;

	if((m = o.readUInt32LE(l)) !== 0x71b2e9f4) return v;
	throw "Unsupported Unicode Extension";
}


function parse_xlscfb(cfb) {
reset_cp();
var CompObj = cfb.find('!CompObj');
var Summary = cfb.find('!SummaryInformation');
var Workbook = cfb.find('/Workbook');
if(!Workbook) Workbook = cfb.find('/Book');
var CompObjP, SummaryP, WorkbookP;


/* 2.4.58 Continue logic */
function slurp(R, blob, length, opts) {
	var read = blob.read_shift.bind(blob);
	var l = length;
	var bufs = [blob.slice(blob.l,blob.l+l)];
	blob.l += length;
	var next = (RecordEnum[blob.readUInt16LE(blob.l)]);
	while(next && next.n === 'Continue') {
		l = blob.readUInt16LE(blob.l+2);
		bufs.push(blob.slice(blob.l+4,blob.l+4+l));
		blob.l += 4+l;
		next = (RecordEnum[blob.readUInt16LE(blob.l)]);
	}
	var b = bconcat(bufs);
	prep_blob(b);
	var ll = 0; b.lens = [];
	bufs.forEach(function(x) { b.lens.push(ll); ll += x.length; });
	return R.f(b, b.length, opts);
}

// 2.3.2
function parse_workbook(blob) {
	var wb = {opts:{}};
	var Sheets = {};
	var out = [];
	var read = blob.read_shift.bind(blob);
	var lst = [], seen = {};
	var Directory = {};
	var found_sheet = false;
	var range = {};
	var last_formula = null;
	var sst = [];
	var cur_sheet = "";
	var Preamble = {};
	var lastcell, last_cell;
	var shared_formulae = {};
	function addline(cell, line) {
		lastcell = cell;
		last_cell = encode_cell(cell);
		out[last_cell] = line;
	}
	var opts = {
		enc: false, // encrypted
		sbcch: 0, // cch in the preceding SupBook
		snames: [], // sheetnames
		sharedf: shared_formulae, // shared formulae by address
		rrtabid: [], // RRTabId
		lastuser: "", // Last User from WriteAccess
		codepage: 0, // CP from CodePage record
		winlocked: 0, // fLockWn from WinProtect
		wtf: false
	};
	var supbooks = [[]]; // 1-indexed, will hold extern names
	var sbc = 0, sbci = 0, sbcli = 0;
	supbooks.SheetNames = opts.snames;
	supbooks.sharedf = opts.sharedf;
	var last_Rn = '';
	var file_depth = 0; /* TODO: make a real stack */
	while(blob.l < blob.length - 1) {
		var s = blob.l;
		var RecordType = read(2);
		if(RecordType === 0 && last_Rn === 'EOF') break;
		var length = (blob.l === blob.length ? 0 : read(2)), y;
		var R = RecordEnum[RecordType];
		if(R && R.f) {
			last_Rn = R.n;
			if(R.r === 2 || R.r == 12) {
				var rt = read(2); length -= 2;
				if(!opts.enc && rt !== RecordType) throw "rt mismatch";
				if(R.r == 12){ blob.l += 10; length -= 10; } // skip FRT
			}
			//console.error(R,blob.l,length,blob.length);
			var val;
			if(R.n === 'EOF') val = R.f(blob, length, opts);
			else val = slurp(R, blob, length, opts);
			switch(R.n) {
				/* Workbook Options */
				case 'Date1904': wb.opts.Date1904 = val; break;
				case 'WriteProtect': wb.opts.WriteProtect = true; break;
				case 'FilePass': opts.enc = val; if(XLS.verbose >= 2) console.error(val); throw new Error("Password protection unsupported"); /* break; */
				case 'WriteAccess': opts.lastuser = val; break;
				case 'FileSharing': break; //TODO
				case 'CodePage':
					opts.codepage = val;
					if(typeof current_codepage !== 'undefined') current_codepage = val;
					if(typeof current_cptable !== 'undefined') current_cptable = cptable[val];
					break;
				case 'RRTabId': opts.rrtabid = val; break;
				case 'WinProtect': opts.winlocked = val; break;
				case 'Template': break; // TODO
				case 'RefreshAll': wb.opts.RefreshAll = val; break;
				case 'BookBool': break; // TODO
				case 'UsesELFs': /* if(val) console.error("Unsupported ELFs"); */ break;
				case 'MTRSettings': {
					if(val[0] && val[1]) throw "Unsupported threads: " + val;
				} break; // TODO: actually support threads
				case 'CalcCount': wb.opts.CalcCount = val; break;
				case 'CalcDelta': wb.opts.CalcDelta = val; break;
				case 'CalcIter': wb.opts.CalcIter = val; break;
				case 'CalcMode': wb.opts.CalcMode = val; break;
				case 'CalcPrecision': wb.opts.CalcPrecision = val; break;
				case 'CalcSaveRecalc': wb.opts.CalcSaveRecalc = val; break;
				case 'CalcRefMode': opts.CalcRefMode = val; break; // TODO: implement R1C1
				case 'Uncalced': break;
				case 'ForceFullCalculation': wb.opts.FullCalc = val; break;
				case 'WsBool': break; // TODO

				case 'Header': break; // TODO
				case 'Footer': break; // TODO
				case 'HCenter': break; // TODO
				case 'VCenter': break; // TODO
				case 'Pls': break; // TODO
				case 'Setup': break; // TODO
				case 'DefColWidth': break; // TODO
				case 'GCW': break;
				case 'LHRecord': break;
				case 'ColInfo': break; // TODO
				case 'Row': break; // TODO
				case 'DBCell': break; // TODO
				case 'MulBlank': break; // TODO
				case 'EntExU2': break; // TODO
				case 'SxView': break; // TODO
				case 'Sxvd': break; // TODO
				case 'SXVI': break; // TODO
				case 'SXVDEx': break; // TODO
				case 'SxIvd': break; // TODO
				case 'SXDI': break; // TODO
				case 'SXLI': break; // TODO
				case 'SXEx': break; // TODO
				case 'QsiSXTag': break; // TODO
				case 'Selection': break;
				case 'Feat': break;
				case 'FeatHdr': case 'FeatHdr11': break;
				case 'Feature11': case 'Feature12': case 'List12': break;
				case 'Blank': break;

				case 'Country': break; // TODO: international support
				case 'RecalcId': break;

				case 'DefaultRowHeight': case 'DxGCol': break; // TODO: htmlify
				case 'Fbi': case 'Fbi2': case 'GelFrame': break;
				case 'Font': break; // TODO
				case 'XF': break; // TODO
				case 'XFCRC': break; // TODO
				case 'XFExt': break; // TODO
				case 'Style': break; // TODO
				case 'StyleExt': break; // TODO
				case 'Palette': break; // TODO
				case 'ClrtClient': break; // TODO
				case 'Theme': break; // TODO

				case 'ExtSST': break; // TODO
				case 'BookExt': break; // TODO
				case 'RichTextStream': break;
				case 'BkHim': break;

				/* Protection */
				case 'ScenarioProtect': break;
				case 'ObjProtect': break;

				/* Conditional Formatting */
				case 'CondFmt12': break;

				/* Table */
				case 'Table': break; // TODO
				case 'TableStyles': break; // TODO

				/* PivotTable */
				case 'SXStreamID': break; // TODO
				case 'SXVS': break; // TODO
				case 'DConRef': break; // TODO
				case 'SXAddl': break; // TODO

				/* Scenario Manager */
				case 'ScenMan': break;

				/* Data Consolidation */
				case 'DCon': break;

				/* Watched Cell */
				case 'CellWatch': break;

				/* Print Settings */
				case 'PrintRowCol': break;
				case 'PrintGrid': break;
				case 'PrintSize': break;

				case 'SupBook': supbooks[++sbc] = [val]; sbci = 0; break;
				case 'ExternName': supbooks[sbc][++sbci] = val; break;
				case 'XCT': break;
				case 'CRN': break;

				case 'Index': break; // TODO
				case 'Lbl': supbooks[0][++sbcli] = val; break;
				case 'ExternSheet': supbooks[sbc] = supbooks[sbc].concat(val); sbci += val.length; break;

				case 'Protect': out["!protect"] = val; break; /* for sheet or book */
				case 'Password': if(val !== 0 && XLS.verbose >= 2) console.error("Password verifier: " + val); break;
				case 'Prot4Rev': case 'Prot4RevPass': break; /*TODO: Revision Control*/

				case 'BoundSheet8': {
					Directory[val.pos] = val;
					opts.snames.push(val.name);
				} break;
				case 'EOF': {
					if(--file_depth) break;
					var nout = {};
					if(range.e) {
						out["!range"] = range;
						if(range.e.r > 0 && range.e.c > 0) {
							range.e.r--; range.e.c--;
							out["!ref"] = encode_range(range);
							range.e.r++; range.e.c++;
						}
					}
					for(y in out) if(out.hasOwnProperty(y)) nout[y] = out[y];
					if(cur_sheet === "") Preamble = nout; else Sheets[cur_sheet] = nout;
				} break;
				case 'BOF': {
					if(file_depth++) break;
					out = {};
					cur_sheet = (Directory[s] || {name:""}).name;
					lst.push([R.n, s, val, Directory[s]]);
				} break;
				case 'Number': {
					addline({c:val.c, r:val.r}, {v:val.val, t:'n'});
				} break;
				case 'BoolErr': {
					addline({c:val.c, r:val.r}, {v:val.val, t:val.t});
				} break;
				case 'RK': {
					addline({c:val.c, r:val.r}, {ixfe: val.ixfe, v:val.rknum, t:'n'});
				} break;
				case 'MulRk': {
					for(var j = val.c; j <= val.C; ++j) {
						addline({c:j, r:val.r}, {ixfe: val.rkrec[j-val.c][0], v:val.rkrec[j-val.c][1], t:'n'});
					}
				} break;
				case 'Formula': {
					switch(val.val) {
						case 'String': last_formula = val; break;
						case 'Array Formula': throw "Array Formula unsupported";
						default: addline(val.cell, {v:val.val, f:stringify_formula(val.formula, range, val.cell, supbooks), ixfe: val.cell.ixfe, t:'n'}); // TODO: infer type from formula
					}
				} break;
				case 'String': {
					if(last_formula) {
						last_formula.val = val;
						addline(last_formula.cell, {v:JSON.stringify(last_formula.val), f:stringify_formula(last_formula.formula, range, last_formula.cell, supbooks), ixfe: last_formula.cell.ixfe, t:'s'});
						last_formula = null;
					}
				} break;
				case 'Array': {
					/* console.error(val); */
				} break;
				case 'ShrFmla': {
					out[last_cell].f = stringify_formula(val[0], range, lastcell, supbooks);
					shared_formulae[last_cell] = val[0];
				} break;
				case 'LabelSst': {
					addline({c:val.c, r:val.r}, {v:JSON.stringify(sst[val.isst]), ixfe:val.ixfe, t:'s'});
				} break;
				case 'Dimensions': {
					range = val;
				} break;
				case 'SST': {
					sst = val;
				} break;
				case 'Format': { /* val = [id, fmt] */
					SSF.load(val[1], val[0]);
				} break;
				case 'Scl': {
					//console.log("Zoom Level:", val[0]/val[1],val);
				} break;
				case 'SheetExt': {

				} break;
				case 'SheetExtOptional': {

				} break;

				/* VBA */
				case 'ObNoMacros': {

				} break;
				case 'ObProj': {

				} break;
				case 'CodeName': {

				} break;
				case 'GUIDTypeLib': {

				} break;
				case 'Note': break;

				case 'MergeCells': break;

				case 'WOpt': break; // TODO: WTF?
				case 'HLink': case 'HLinkTooltip': break;

				case 'PhoneticInfo': break;

				case 'OleObjectSize': break;

				case 'TxO': break;

				/* Differential Formatting */
				case 'DXF': case 'DXFN': case 'DXFN12': case 'DXFN12List': case 'DXFN12NoCB': break;

				/* Data Validation */
				case 'Dv': case 'DVal': break;

				/* Data Series */
				case 'BRAI': case 'Series': case 'SeriesText': break;

				/* Data Connection */
				case 'DConn': break;
				case 'DbOrParamQry': break;
				case 'DBQueryExt': break;

				/* Formatting */
				case 'IFmtRecord': break;
				case 'CondFmt': case 'CF': case 'CF12': case 'CFEx': break;

				/* Comments */
				case 'NameCmt': break;

				/* Chart */
				case 'Dat':
				case 'Begin': case 'End':
				case 'StartBlock': case 'EndBlock':
				case 'Frame': case 'Area':
				case 'Axis': case 'AxisLine': case 'Tick': break;
				case 'AxesUsed':
				case 'CrtLayout12': case 'CrtLayout12A': case 'CrtLink': case 'CrtLine': case 'CrtMlFrt': break;
				case 'LineFormat': case 'AreaFormat':
				case 'Chart': case 'Chart3d': case 'Chart3DBarShape': case 'ChartFormat': case 'ChartFrtInfo': break;
				case 'PlotArea': case 'PlotGrowth': break;
				case 'SeriesList': case 'SerParent': case 'SerAuxTrend': break;
				case 'DataFormat': case 'SerToCrt': case 'FontX': break;
				case 'CatSerRange': case 'AxcExt': case 'SerFmt': break;
				case 'ShtProps': break;
				case 'DefaultText': case 'Text': case 'Label': case 'CatLab': break;
				case 'DataLabExtContents': break;
				case 'Legend': case 'LegendException': break;
				case 'Pie': case 'Scatter': break;
				case 'PieFormat': case 'MarkerFormat': break;
				case 'StartObject': case 'EndObject': break;
				case 'AlRuns': case 'ObjectLink': break;
				case 'SIIndex': break;
				case 'AttachedLabel': break;
				/* Chart Group */
				case 'Line': case 'Bar': break;
				case 'Surf': break;
				/* Axis Group */
				case 'AxisParent': break;
				case 'Pos': break;
				case 'ValueRange': break;
				/* Pivot Chart */
				case 'SXViewEx9': break; // TODO
				case 'SXViewLink': break;
				case 'PivotChartBits': break;
				case 'SBaseRef': break;
				case 'TextPropsStream': break;
				/* Chart Misc */
				case 'LnExt': break;
				case 'MkrExt': break;
				case 'CrtCoopt': break;
				/* Query Table */
				case 'Qsi': case 'Qsif': case 'Qsir': case 'QsiSXTag': break;
				case 'TxtQry': break;

				/* Filter */
				case 'FilterMode': break;
				case 'AutoFilter': case 'AutoFilterInfo': break;
				case 'DropDownObjIds': break;
				case 'Sort': break;
				case 'SortData': break;
				/* Drawing */
				case 'ShapePropsStream': break;
				case 'MsoDrawing': case 'MsoDrawingGroup': case 'MsoDrawingSelection': break;
				case 'Obj': break;
				case 'ImData': break;
				/* Explicitly Ignored */
				case 'Excel9File': break;
				case 'Units': break;
				case 'InterfaceHdr': case 'Mms': case 'InterfaceEnd': case 'DSF': case 'BuiltInFnGroupCount':
				/* View Stuff */
				case 'Window1': case 'Window2': case 'HideObj': case 'GridSet': case 'Guts':
				case 'UserBView': case 'UserSViewBegin': case 'UserSViewEnd':
				case 'Pane':
				/* Pub Stuff */
				case 'WebPub': case 'AutoWebPub':
				/* Print Stuff */
				case 'RightMargin': case 'LeftMargin': case 'TopMargin': case 'BottomMargin':
				case 'HeaderFooter': case 'HFPicture': case 'PLV':
				case 'HorizontalPageBreaks': case 'VerticalPageBreaks':
				/* Behavioral */
				case 'Backup': case 'CompressPictures': case 'Compat12': break;

				/* Should not Happen */
				case 'Continue': case 'ContinueFrt12': break;
				/* Uncomment next line in development */
				default: throw 'Unrecognized Record ' + R.n;
			}
			lst.push([R.n, s, val]);
			continue;
		}
		lst.push(['Unrecognized', Number(RecordType).toString(16), RecordType]);
		read(length);
	}
	var sheetnamesraw = Object.keys(Directory).sort(function(a,b) { return Number(a) - Number(b); }).map(function(x){return Directory[x].name;});
	var sheetnames = []; sheetnamesraw.forEach(function(x){sheetnames.push(x);});
	//console.log(lst);
	//lst.filter(function(x) { return x[0] === 'Formula';}).forEach(function(x){console.log(x[2].cell,x[2].formula);});
	wb.Directory=sheetnamesraw;
	wb.SheetNames=sheetnamesraw;
	wb.Sheets=Sheets;
	wb.Preamble=Preamble;
	wb.Strings = sst;
	if(opts.enc) wb.Encryption = opts.enc;
	return wb;
}
if(Workbook) WorkbookP = parse_workbook(Workbook.content);
else throw new Error("Cannot find Workbook stream");
if(CompObj) CompObjP = parse_compobj(CompObj);

return WorkbookP;
}

function sheet_to_row_object_array(sheet){
	var val, rowObject, range, columnHeaders, emptyRow, C;
	var outSheet = [];
	if (sheet["!ref"]) {
		range = decode_range(sheet["!ref"]);

		columnHeaders = {};
		for (C = range.s.c; C <= range.e.c; ++C) {
			val = sheet[encode_cell({
				c: C,
				r: range.s.r
			})];
			if(val){
				switch(val.t) {
					case 's': case 'str': columnHeaders[C] = JSON.parse(val.v); break;
					case 'n': columnHeaders[C] = val.v; break;
				}
			}
		}

		for (var R = range.s.r + 1; R <= range.e.r; ++R) {
			emptyRow = true;
			//Row number is recorded in the prototype
			//so that it doesn't appear when stringified.
			rowObject = Object.create({ __rowNum__ : R });
			for (C = range.s.c; C <= range.e.c; ++C) {
				val = sheet[encode_cell({
					c: C,
					r: R
				})];
				var v = (val || {}).v;
				if(val !== undefined) switch(val.t){
					case 's': case 'str':
						if(v !== undefined) v = JSON.parse(v);
					/* falls through */
					case 'b': case 'n':
						if(v !== undefined) {
							rowObject[columnHeaders[C]] = v;
							emptyRow = false;
						}
						break;
					case 'e': break; /* throw */
					default: throw 'unrecognized type ' + val.t;
				}
			}
			if(!emptyRow) {
				outSheet.push(rowObject);
			}
		}
	}
	return outSheet;
}

function sheet_to_csv(sheet) {
	var out = "";
	if(sheet["!ref"]) {
		var r = utils.decode_range(sheet["!ref"]);
		for(var R = r.s.r; R <= r.e.r; ++R) {
			var row = [];
			for(var C = r.s.c; C <= r.e.c; ++C) {
				var val = sheet[utils.encode_cell({c:C,r:R})];
				if(!val) { row.push(""); continue; }
				if(typeof val.v === 'boolean') val.v = val.v ? "TRUE" : "FALSE";
				row.push(String(val.v).replace(/\\\\n/g,"\\n").replace(/\\\\t/g,"\\t").replace(/\\\\\\\\/g,"\\\\").replace(/\\\\\\"/g,"\\"\\""));
			}
			out += row.join(",") + "\\n";
		}
	}
	return out;
}
var make_csv = sheet_to_csv;

function get_formulae(ws) {
	var cmds = [];
	for(var y in ws) if(y[0] !=='!' && ws.hasOwnProperty(y)) {
		var x = ws[y];
		var val = "";
		if(x.f) val = x.f;
		else if(typeof x.v === 'number') val = x.v;
		else val = x.v;
		cmds.push(y + "=" + val);
	}
	return cmds;
}

var utils = {
	encode_col: encode_col,
	encode_row: encode_row,
	encode_cell: encode_cell,
	encode_range: encode_range,
	decode_col: decode_col,
	decode_row: decode_row,
	split_cell: split_cell,
	decode_cell: decode_cell,
	decode_range: decode_range,
	sheet_to_csv: sheet_to_csv,
	make_csv: sheet_to_csv,
	get_formulae: get_formulae,
	sheet_to_row_object_array: sheet_to_row_object_array
};

function xlsread(f, options) {
	return parse_xlscfb(CFB.read(f, options));
}
var readFile = function(f) { return parse_xlscfb(CFB.read(f, {type:'file'})); };
function decode_row(rowstr) { return Number(unfix_row(rowstr)) - 1; }
function encode_row(row) { return "" + (row + 1); }
function fix_row(cstr) { return cstr.replace(/([A-Z]|^)([0-9]+)$/,"$1$$$2"); }
function unfix_row(cstr) { return cstr.replace(/\\$([0-9]+)$/,"$1"); }

function decode_col(colstr) { var c = unfix_col(colstr), d = 0, i = 0; for(; i !== c.length; ++i) d = 26*d + c.charCodeAt(i) - 64; return d - 1; }
function encode_col(col) { var s=""; for(++col; col; col=Math.floor((col-1)/26)) s = String.fromCharCode(((col-1)%26) + 65) + s; return s; }
function fix_col(cstr) { return cstr.replace(/^([A-Z])/,"$$$1"); }
function unfix_col(cstr) { return cstr.replace(/^\\$([A-Z])/,"$1"); }

function split_cell(cstr) { return cstr.replace(/(\\$?[A-Z]*)(\\$?[0-9]*)/,"$1,$2").split(","); }

/* decode_cell assumes that you are passing a valid cell (not a row/col) */
function decode_cell(cstr) { var splt = split_cell(cstr); return { c:decode_col(splt[0]), r:decode_row(splt[1]) }; }
function encode_cell(cell) { return encode_col(cell.c) + encode_row(cell.r); }
function fix_cell(cstr) { return fix_col(fix_row(cstr)); }
function unfix_cell(cstr) { return unfix_col(unfix_row(cstr)); }

/* ranges can be individual cells -- magic happens here */
function decode_range(range) { var x =range.split(":").map(decode_cell); return {s:x[0],e:x[x.length-1]}; }
function encode_range(cs,ce) {
	if(typeof ce === 'undefined' || typeof ce === 'number') return encode_range(cs.s, cs.e);
	if(typeof cs !== 'string') cs = encode_cell(cs); if(typeof ce !== 'string') ce = encode_cell(ce);
	return cs == ce ? cs : cs + ":" + ce;
}

function shift_cell(cell, tgt) {
	if(tgt.s) {
		if(cell.cRel) cell.c += tgt.s.c;
		if(cell.rRel) cell.r += tgt.s.r;
	} else {
		cell.c += tgt.c;
		cell.r += tgt.r;
	}
	cell.cRel = cell.rRel = 0;
	while(cell.c >= 0x100) cell.c -= 0x100;
	while(cell.r >= 0x10000) cell.r -= 0x10000;
	return cell;
}

function shift_range(cell, range) {
	cell.s = shift_cell(cell.s, range.s);
	cell.e = shift_cell(cell.e, range.s);
	return cell;
}

XLS.parse_xlscfb = parse_xlscfb;
XLS.read = xlsread;
XLS.readFile = readFile;
XLS.utils = utils;
XLS.CFB = CFB;
if(typeof module !== 'undefined' && require.main === module ) {
	var wb = readFile(process.argv[2] || 'Book1.xls');
	var target_sheet = process.argv[3] || '';
	if(target_sheet === '') target_sheet = wb.Directory[0];
	var ws = wb.Sheets[target_sheet];
	console.log(target_sheet);
	console.log(make_csv(ws));
	//console.log(get_formulae(ws));
}
})(typeof exports !== 'undefined' ? exports : XLS);
"""

utils = Utils();

if "__main__" == __name__:
	from sys import argv, stderr
	WB = XLSFile();
	jswb = WB.readfile(argv[1]);
	print >>stderr, WB.sheetnames() 
	print utils.csvify(WB.sheet(1))
