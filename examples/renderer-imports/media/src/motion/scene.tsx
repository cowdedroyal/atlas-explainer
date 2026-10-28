import {Circle, makeScene2D} from '@motion-canvas/2d';
import {createRef} from '@motion-canvas/core';
export default makeScene2D(function* (view) {
  const dot = createRef<Circle>();
  view.add(<Circle ref={dot} x={-100} size={40} fill={'#6aa9cf'}/>);
  yield* dot().position.x(100, 1);
});
