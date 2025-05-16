-- --------------------
-- Fill database with data
-- --------------------

INSERT INTO ATTENDANCE_TYPES(name) VALUES('Obecny'), ('Nieobecny'), ('Usprawiedliwiony');
INSERT INTO GENDERS(name) VALUES('kobieta'), ('mężczyzna'), ('dziewczynka'), ('chłopiec');

INSERT INTO FAMILY_MEMBERS(name) VALUES('Dziecko'),('Rodzic'),('Małżonek'),('Brat'),('Siostra'),('Kuzyn'),('Inny') ON CONFLICT (name) DO NOTHING;
