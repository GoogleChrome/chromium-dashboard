/**
 * Copyright 2013 Google Inc. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
var target = document.querySelector('#target');
var visualParent = document.querySelector('#visual-parent');

target.addEventListener('touchstart', function(e) {
  e.preventDefault();
  target.textContent = e.touches.length;
  if (e.touches.length == e.changedTouches.length) {
    onFirstTouchStart(e);
  }
});

target.addEventListener('touchmove', function(e) {
  onTouchMove(e);
});

target.addEventListener('touchend', function(e) {
  onTouchEnd(e);
  if (e.touches.length == 0) {
    target.textContent = '';
  } else {
    target.textContent = e.touches.length;
  }
});

var fadeTime = 0.085;
var visible = [{opacity: 1}, {opacity: 1}];
var fadeIn = [{opacity: 0}, {opacity: 1}];
var fadeOut = [{opacity: 1}, {opacity: 0}];

var touchStart;
var visuals;
var recordedTouches;
var group;
var player;

function onFirstTouchStart(e) {
  touchStart = e.timeStamp;
  recordedTouches = {};
  visuals && visuals.forEach(function(visual) {
    visual.remove();
  });
  visuals = [];
  group = new ParGroup([], {direction: 'alternate', iterations: Infinity});
  if (player) {
    player.source = null;
  }
  onTouchMove(e);
}

function onTouchMove(e) {
  for (var i = 0; i < e.changedTouches.length; i++) {
    var touch = e.changedTouches[i];
    if (!recordedTouches[touch.identifier]) {
      var start = e.timeStamp - touchStart;
      recordedTouches[touch.identifier] = [];
    }
    recordedTouches[touch.identifier].push({
      x: touch.clientX,
      y: touch.clientY,
      time: e.timeStamp - touchStart,
    });
  }
}

function onTouchEnd(e) {
  for (var i = 0; i < e.changedTouches.length; i++) {
    var id = e.changedTouches[i].identifier;
    if (!recordedTouches[id] || recordedTouches[id].length <= 1) {
      continue;
    }
    var startTime = recordedTouches[id][0].time;
    var duration = recordedTouches[id][recordedTouches[id].length - 1].time - startTime;
    var endTime = startTime + duration;
    var frames = recordedTouches[id].map(function(touch) {
      return {
        transform: 'translateZ(0) translate(' + touch.x + 'px, ' + touch.y + 'px)',
        offset: (touch.time - startTime) / duration,
      };
    });
    recordedTouches[id] = null;
    
    var visual;
    for (var i = 0; i < visuals.length; i++) {
      if (visuals[i].endTime < startTime) {
        visual = visuals[i];
        break;
      }
    }
    if (!visual) {
      visual = document.createElement('div');
      visual.endTime = endTime;
      visual.classList.add('visual');
      visuals.push(visual);
      visualParent.appendChild(visual);
    }
    var durationS = duration / 1000;
    var startTimeS = startTime / 1000;
    group.append(new ParGroup([
      new Animation(visual, visible, {duration: durationS, fill: 'none'}),
      new Animation(visual, fadeOut, {duration: fadeTime, delay: durationS - fadeTime, fill: 'none'}),
      new Animation(visual, fadeIn, {duration: fadeTime, fill: 'none'}),
      new Animation(visual, frames, {duration: durationS, fill: 'none'}),
    ], {duration: durationS, delay: startTimeS}));
  }
  
  if (e.touches.length == 0) {
    player = document.timeline.play(group);
  }
};