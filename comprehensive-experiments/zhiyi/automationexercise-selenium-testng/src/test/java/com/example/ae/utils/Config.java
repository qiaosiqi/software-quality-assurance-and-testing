package com.example.ae.utils;

import org.testng.ITestContext;

import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;

/**
 * 参数优先级：
 * 1. 命令行 -Dxxx=yyy
 * 2. TestNG XML <parameter>
 * 3. config.properties
 * 4. 代码中的兜底默认值
 */
public final class Config {
    private static final Properties PROPERTIES = new Properties();

    static {
        try (InputStream in = Config.class.getClassLoader().getResourceAsStream("config.properties")) {
            if (in != null) {
                PROPERTIES.load(in);
            }
        } catch (IOException e) {
            throw new RuntimeException("读取 config.properties 失败", e);
        }
    }

    private Config() {}

    public static String get(ITestContext context, String key, String defaultValue) {
        String systemValue = System.getProperty(key);
        if (systemValue != null && !systemValue.isBlank() && !"null".equalsIgnoreCase(systemValue)) {
            return systemValue.trim();
        }

        if (context != null && context.getCurrentXmlTest() != null) {
            String testngValue = context.getCurrentXmlTest().getParameter(key);
            if (testngValue != null && !testngValue.isBlank()) {
                return testngValue.trim();
            }
        }

        String fileValue = PROPERTIES.getProperty(key);
        if (fileValue != null && !fileValue.isBlank()) {
            return fileValue.trim();
        }

        return defaultValue;
    }

    public static int getInt(ITestContext context, String key, int defaultValue) {
        try {
            return Integer.parseInt(get(context, key, String.valueOf(defaultValue)));
        } catch (NumberFormatException e) {
            return defaultValue;
        }
    }

    public static boolean getBoolean(ITestContext context, String key, boolean defaultValue) {
        return Boolean.parseBoolean(get(context, key, String.valueOf(defaultValue)));
    }

    public static String normalizeBaseUrl(String raw) {
        if (raw == null || raw.isBlank()) {
            return "https://automationexercise.com";
        }
        String url = raw.trim();
        int hashIndex = url.indexOf('#');
        if (hashIndex >= 0) {
            url = url.substring(0, hashIndex);
        }
        while (url.endsWith("/")) {
            url = url.substring(0, url.length() - 1);
        }
        return url;
    }
}
