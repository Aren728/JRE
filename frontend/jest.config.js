const nextJest = require('next/jest');

const createJestConfig = nextJest({
  dir: './',
});

const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  testEnvironment: 'jest-environment-jsdom',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
    // next/jest always ignores node_modules transforms, so the ESM-only
    // OrbitControls can never be transformed — map it to a Jest stub.
    'three/examples/jsm/controls/OrbitControls.js': '<rootDir>/__mocks__/OrbitControlsStub.ts',
  },
  testPathIgnorePatterns: ['/node_modules/', '/e2e/'],
  transformIgnorePatterns: [
    '/node_modules/(?!(react-markdown|vfile|vfile-message|unist-.*|unified|bail|is-plain-obj|trough|remark-.*|mdast-util-.*|micromark.*|decode-named-character-reference|character-entities|property-information|hast-util-.*|space-separated-tokens|comma-separated-tokens|estree-util-.*)/)',
  ],
};

module.exports = createJestConfig(customJestConfig);
