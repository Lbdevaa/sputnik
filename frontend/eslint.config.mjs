import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";
import prettier from "eslint-config-prettier";

const config = [
  ...nextVitals,
  ...nextTs,
  prettier,
  {
    ignores: [".next/**", "node_modules/**", "next-env.d.ts"],
  },
  {
    rules: {
      // Слои: нижний не импортирует верхний. Проверяется путями импортов.
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["@/app/*"],
              message: "app/ — точка сборки, из него ничего не импортируют.",
            },
          ],
        },
      ],
    },
  },
  {
    files: ["src/shared/**"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["@/entities/*", "@/features/*", "@/widgets/*", "@/app/*"],
              message: "shared/ не знает про слои выше.",
            },
          ],
        },
      ],
    },
  },
  {
    files: ["src/entities/**"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["@/features/*", "@/widgets/*", "@/app/*"],
              message: "entities/ не знает про features, widgets и app.",
            },
          ],
        },
      ],
    },
  },
  {
    files: ["src/features/**"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["@/widgets/*", "@/app/*"],
              message: "features/ не знает про widgets и app.",
            },
          ],
        },
      ],
    },
  },
];

export default config;
