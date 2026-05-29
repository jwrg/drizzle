function setBubble(range, bubble) {
  const val = range.value;
  const min = range.min ? range.min : 0;
  const max = range.max ? range.max : 100;
  const newVal = Number(((val - min) * 100) / (max - min));
  bubble.innerHTML = val == 1 ? val + '&nbsp;minute' : val + '&nbsp;minutes';
  bubble.style.left = `calc(${newVal}% + (${8 - newVal * 0.15}px))`;
}

function get_seconds(time_string) {
  let time_array = time_string.split(':').map(x => Number(x));
  if (time_array.length === 2) {
    time_array[0] = time_array[0] * 60;
  } else {
    time_array[0] = time_array[0] * 3600;
    time_array[1] = time_array[1] * 60;
  }
  return time_array.reduce((acc, curr) => acc + curr, 0);
}

function format_seconds(remaining) {
  const seconds = remaining % 60 < 10 ? '0' + Math.floor(remaining % 60).toString() : Math.floor(remaining % 60).toString();
  const minutes = (remaining / 60) % 60 < 10 ? '0' + Math.floor((remaining / 60) % 60).toString() : Math.floor((remaining / 60) % 60).toString();
  const hours = Math.floor(remaining / 3600).toString();
  return hours === '0' ? minutes + ':' + seconds : hours + ':' + minutes + ':' + seconds;
}

function set_countdown(el) {
  el.innerHTML = format_seconds(el.innerHTML);
  return setInterval(function() {
    seconds = Number(get_seconds(el.innerHTML));
    if (seconds <= 0 || seconds === NaN) {
      // console.log(seconds);
      window.location.reload();
    } else {
      el.innerHTML = format_seconds(seconds - 1);
    }
  }, 999);
}

function set_countup(el) {
  var current = new Date();
  el.innerHTML = current.toLocaleString();
  return setInterval(function() {
    current.setSeconds(current.getSeconds() + 1);
    el.innerHTML = current.toLocaleString();
  }, 999);
}

const running_buttons = Array.from(document.getElementsByClassName('running-label'));
var datetime = set_countup(document.getElementById('datetime'));
let handles = [];
for (let i = 0; i < running_buttons.length; ++i) {
  handles[i] = set_countdown(running_buttons[i]);
}
