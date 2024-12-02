create database biblioteca;
use biblioteca;

create table Livros(
	id_livro int primary key auto_increment not null,
    nome_livro varchar(120) not null,
    autor_livro varchar(100) not null,
    data_publicacao_livro date not null,
    quantidade_paginas_livro int not null,
    editora_livro varchar(50) not null,
    genero_livro varchar(50) not null,
    classificacao_livro int not null,
    isbn_livro bigint not null,
    data_cadastro_livro date not null,
    foto_livro varchar(50) not null, 
    status_livro enum('Alugado', 'Disponível') not null
);

insert into Livros (nome_livro, autor_livro, data_publicacao_livro, quantidade_paginas_livro, editora_livro, genero_livro, classificacao_livro, isbn_livro, data_cadastro_livro, status_livro, foto_livro)
values ('A Rainha Vermelha', 'Victoria Aveyard', '2015-06-09', 424, 'Editora Seguinte', 'Romance e Fantasia', 14, 9788565765695, '2024-09-12', 'Alugado', 'rainha.jpg');

create table Usuarios(
	id_usuario int primary key auto_increment,
    nome_usuario varchar(225) not null,
    cpf_usuario varchar(200) not null unique,
    idade_usuario int not null,
    telefone_usuario varchar(11) not null,
    email_usuario varchar(200) not null,
    senha_usuario varchar(200) not null,
    funcao_usuario enum ('administrador', 'cliente'),
    cep_usuario varchar(10) not null,
    numero_casa_usuario varchar(8) not null, 
    salt varchar(250)
);

insert into Usuarios (nome_usuario, cpf_usuario, idade_usuario, telefone_usuario, email_usuario, senha_usuario, funcao_usuario, cep_usuario, numero_casa_usuario)
values ('Livia Almeida', SHA2('21568403257', '256'), 17, '15998381280', 'livinha@hotmail.com', SHA2('123456789', '256'), 'cliente', '01153000', '12'),
	   ('Stella Maris', SHA2('12312312312', '256'), 16, '1599589799', 'stella_maris@gmail.com', SHA2('12345', 256), 'administrador', '15264000', '52');



create table Emprestimos(
	id_emprestimo int primary key auto_increment not null,
    data_emprestimo_livro date not null,
    data_devolucao_prevista date not null,
    data_devolucao_real date,
    id_livro_FK int not null,
    id_usuario_FK int not null,
    foreign key (id_livro_FK) references Livros(id_livro),
    foreign key (id_usuario_FK) references Usuarios(id_usuario)
);

insert into Emprestimos (data_emprestimo_livro, data_devolucao_prevista, data_devolucao_real, id_livro_FK, id_usuario_FK)
values ('2024-09-12', '2024-09-13', '2024-09-19', 1, 1);

DELIMITER //

CREATE TRIGGER att_estado_livro_insert
BEFORE INSERT ON Emprestimos
FOR EACH ROW
BEGIN
    IF NEW.data_devolucao_real IS NOT NULL AND NEW.data_devolucao_real <= CURRENT_DATE() THEN
        UPDATE Livros 
        SET status_livro = 'Disponível'
        WHERE Livros.id_livro = NEW.id_livro_FK;
    ELSE
        UPDATE Livros 
        SET status_livro = 'Alugado'
        WHERE Livros.id_livro = NEW.id_livro_FK;
    END IF;
END;
//

DELIMITER ;


DELIMITER //

CREATE TRIGGER att_estado_livro_update
BEFORE UPDATE ON Emprestimos
FOR EACH ROW
BEGIN
    IF NEW.data_devolucao_real IS NOT NULL AND NEW.data_devolucao_real <= CURRENT_DATE() THEN
        UPDATE Livros 
        SET status_livro = 'Disponível'
        WHERE Livros.id_livro = NEW.id_livro_FK;
    ELSE
        UPDATE Livros 
        SET status_livro = 'Alugado'
        WHERE Livros.id_livro = NEW.id_livro_FK;
    END IF;
END;
//

DELIMITER ;
use biblioteca;
select * from Usuarios;