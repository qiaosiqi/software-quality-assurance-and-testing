package com.example.ae.utils;

import com.example.ae.model.UserData;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Locale;
import java.util.concurrent.ThreadLocalRandom;

/**
 * 测试数据工厂：邮箱每次动态生成，避免重复注册导致失败。
 */
public final class TestDataFactory {
    private TestDataFactory() {}

    public static String uniqueEmail(String domain) {
        String safeDomain = (domain == null || domain.isBlank()) ? "example.com" : domain.trim();
        String time = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMddHHmmssSSS", Locale.ROOT));
        int rand = ThreadLocalRandom.current().nextInt(1000, 9999);
        return "ae_" + time + "_" + rand + "@" + safeDomain;
    }

    public static UserData newUser(String name, String password, String emailDomain) {
        return UserData.builder()
                .name(name)
                .email(uniqueEmail(emailDomain))
                .password(password)
                .firstName(name.split(" ")[0])
                .lastName("Auto")
                .company("Selenium Lab")
                .address("No. 1 Automation Road")
                .country("United States")
                .state("California")
                .city("Los Angeles")
                .zipcode("90001")
                .mobileNumber("13800000000")
                .day("1")
                .month("January")
                .year("2000")
                .build();
    }
}
