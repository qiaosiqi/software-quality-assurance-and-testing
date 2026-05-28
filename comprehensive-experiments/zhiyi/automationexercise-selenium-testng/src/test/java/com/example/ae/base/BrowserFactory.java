package com.example.ae.base;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.PageLoadStrategy;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.edge.EdgeDriver;
import org.openqa.selenium.edge.EdgeOptions;
import org.openqa.selenium.firefox.FirefoxDriver;
import org.openqa.selenium.firefox.FirefoxOptions;

/**
 * 浏览器工厂。browser/headless 均从外部参数传入，不在测试用例里写死。
 */
public final class BrowserFactory {
    private BrowserFactory() {}

    public static WebDriver createDriver(String browser, boolean headless) {
        String normalized = browser == null ? "chrome" : browser.trim().toLowerCase();

        switch (normalized) {
            case "firefox":
                FirefoxOptions firefoxOptions = new FirefoxOptions();
                firefoxOptions.setPageLoadStrategy(PageLoadStrategy.EAGER);
                if (headless) {
                    firefoxOptions.addArguments("-headless");
                }
                return new FirefoxDriver(firefoxOptions);

            case "edge":
                EdgeOptions edgeOptions = new EdgeOptions();
                if (headless) {
                    edgeOptions.addArguments("--headless=new");
                    edgeOptions.addArguments("--window-size=1440,1000");
                    edgeOptions.setPageLoadStrategy(PageLoadStrategy.EAGER);
                }
                return new EdgeDriver(edgeOptions);

            case "chrome":
            default:
                ChromeOptions chromeOptions = new ChromeOptions();
                chromeOptions.addArguments("--remote-allow-origins=*");
                chromeOptions.addArguments("--disable-notifications");
                chromeOptions.addArguments("--disable-popup-blocking");
                chromeOptions.addArguments("--window-size=1440,1000");
                chromeOptions.addArguments("--disable-extensions");
                chromeOptions.addArguments("--disable-blink-features=AutomationControlled");
                chromeOptions.setPageLoadStrategy(PageLoadStrategy.EAGER);
                if (headless) {
                    chromeOptions.addArguments("--headless=new");
                    chromeOptions.addArguments("--disable-gpu");
                }
                return new ChromeDriver(chromeOptions);
        }
    }
}
