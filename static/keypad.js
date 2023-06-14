document.getElementById("time").addEventListener("input", () => {
  setBubble(document.getElementById("time"),document.getElementById("time").nextElementSibling);
});
setBubble(document.getElementById("time"),document.getElementById("time").nextElementSibling);

function setBubble(range, bubble) {
  const val = range.value;
  const min = range.min ? range.min : 0;
  const max = range.max ? range.max : 100;
  const newVal = Number(((val - min) * 100) / (max - min));
  bubble.innerHTML = val == 1 ? val + ' minute' : val + ' minutes';
  bubble.style.left = `calc(${newVal}% + (${8 - newVal * 0.15}px))`;
}
