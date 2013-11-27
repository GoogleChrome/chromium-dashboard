timing_test(function() {
  at(0, function() {
    assert_styles(".anim",{'left':'0px'});
  });
  at(0.5, function() {
    assert_styles(".anim",{'left':'0px'});
  });
  at(1, function() {
    assert_styles(".anim",{'left':'0px'});
  });
  at(1.5, function() {
    assert_styles(".anim", [
      {'left':'86.37px'},
      {'left':'393.4px'},
      {'left':'31.54px'},
      {'left':'295.9px'},
      {'left':'12.5px'},
      {'left':'329.1px'},
      {'left':'80.24px'},
      {'left':'393.4px'},
    ]);
  });
  at(2, function() {
    assert_styles(".anim", [
      {'left':'138.7px'},
      {'left':'330.8px'},
      {'left':'100px'},
      {'left':'330.8px'},
      {'left':'100px'},
      {'left':'350px'},
      {'left':'100px'},
      {'left':'355.6px'},
    ]);
  });
  at(2.5, function() {
    assert_styles(".anim", [
      {'left':'150px'},
      {'left':'239.5px'},
      {'left':'180.2px'},
      {'left':'239.5px'},
      {'left':'150px'},
      {'left':'300px'},
      {'left':'150px'},
      {'left':'300px'},
    ]);
  });
  at(3, function() {
    assert_styles(".anim", [
      {'left':'236.4px'},
      {'left':'206.1px'},
      {'left':'200px'},
      {'left':'206.1px'},
      {'left':'200px'},
      {'left':'250px'},
      {'left':'200px'},
      {'left':'244.4px'},
    ]);
  });
  at(3.5, function() {
    assert_styles(".anim", [
      {'left':'288.7px'},
      {'left':'222.1px'},
      {'left':'268.5px'},
      {'left':'226px'},
      {'left':'250px'},
      {'left':'216.7px'},
      {'left':'250px'},
      {'left':'221.8px'},
    ]);
  });
  at(4, function() {
    assert_styles(".anim",{'left':'300px'});
  });
}, "Auto generated tests");