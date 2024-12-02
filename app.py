from flask import Flask, render_template, request, redirect, url_for, flash, make_response, session
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import pymysql, hashlib, secrets
import os
import re 
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = '9b7f0bbd0cf9b05caf200ff36e753ea4'

UPLOAD_FOLDER = 'static/capas'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

connection = pymysql.connect(
    host='localhost',
    user='root',
    password='Papayankee2',
    database='biblioteca', 
    port=3306
)

cursor = connection.cursor()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/verificar', methods=['POST'])
def verificar():
    email = request.form['email_usuario']
    senha = request.form['senha_usuario']


    if not email:
        flash('O campo de e-mail é obrigatório.')
        return render_template('login.html')

    try:
        with connection.cursor() as cursor:
            command = "SELECT funcao_usuario, senha_usuario, salt FROM Usuarios WHERE email_usuario = %s;"
            cursor.execute(command, (email,))
            resultado = cursor.fetchone() 

            if resultado:
                funcao_usuario, senha_armazenada, salt_armazenado = resultado
                senha_gerada = hash_senha(senha, salt_armazenado)

                session['email'] = email

                if senha_armazenada == senha_gerada: 
                    if funcao_usuario == 'administrador': 
                        return render_template('pagInicio.html')
                    elif funcao_usuario == 'cliente':
                        return render_template('pagCliente.html')
                
                else: 
                    flash('Senha incorreta!')
                    return render_template('login.html')
            else:
                flash('Email incorreto ou ainda não cadastrado.')
                return render_template('login.html') 
    except Exception as e:
        flash('Erro ao verificar o login.')
        return render_template('login.html') 
        
    session['email'] = email


@app.route('/sair')
def sair():
    return render_template('index.html')


@app.route('/livros')
def livros():
    command = 'SELECT * FROM Livros;'
    cursor.execute(command)
    livros = cursor.fetchall()

    today = datetime.now().date()

    return render_template('livros.html', livros=livros, today=today)

@app.route('/usuarios')
def usuarios():
    command = 'SELECT * FROM Usuarios;'
    cursor.execute(command)
    usuarios = cursor.fetchall()
    
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/emprestimos')
def emprestimos():
    command = 'SELECT * FROM Emprestimos;'
    cursor.execute(command)
    emprestimos = cursor.fetchall()

    command = 'SELECT * FROM Livros;'
    cursor.execute(command)
    livros = cursor.fetchall()

    command = 'SELECT * FROM Usuarios;'
    cursor.execute(command)
    usuarios = cursor.fetchall()

    today = datetime.now().date()
    
    return render_template('emprestimos.html', emprestimos=emprestimos, livros=livros, usuarios=usuarios, today=today)

@app.route('/pagInicio')
def pagInicio():
    return render_template('pagInicio.html')

@app.route('/pagCliente')
def pagCliente():
    return render_template('pagCliente.html')

@app.route('/perfil')
def perfil():
    email = session.get('email')

    if not email:
        flash('Usuário não autenticado. Faça login novamente')
        return render_template('login.html')
    
    try:
        with connection.cursor() as cursor:
            command = 'SELECT * FROM Usuarios WHERE email_usuario = %s'
            cursor.execute(command, (email,))
            usuario = cursor.fetchone()

            if usuario:
                return render_template('perfil.html', usuario=usuario)
            else:
                flash('Usuário não encontrado')
                return render_template('login.html')
    except Exception as e:
        flash('Erro ao buscar as informações do perfil')
        return render_template('login.html')

@app.route('/perfilAdm')
def perfilAdm():
    email = session.get('email')

    if not email:
        flash('Usuário não autenticado. Faça login novamente')
        return render_template('login.html')
    
    try:
        with connection.cursor() as cursor:
            command = 'SELECT * FROM Usuarios WHERE email_usuario = %s'
            cursor.execute(command, (email,))
            usuario = cursor.fetchone()

            if usuario:
                return render_template('perfilAdm.html', usuario=usuario)
            else:
                flash('Usuário não encontrado')
                return render_template('login.html')
    except Exception as e:
        flash('Erro ao buscar as informações do perfil')
        return render_template('login.html')

@app.route('/meusEmprestimos')
def meusEmprestimos():
    email = session.get('email')

    if not email:
        flash('O email é obrigatório')
        return render_template('login.html')
    
    try:
        with connection.cursor() as cursor:
            # Buscar o ID do usuário com base no email
            command_usuario = "SELECT id_usuario FROM Usuarios WHERE email_usuario = %s;"
            cursor.execute(command_usuario, (email,))
            usuario = cursor.fetchone()

            if not usuario:
                flash('Usuário não encontrado')
                return render_template('login.html')
            
            id_usuario_FK = usuario[0]
            command_emprestimos = """
                SELECT 
                Emprestimos.id_emprestimo,
                Emprestimos.data_emprestimo_livro,
                Emprestimos.data_devolucao_prevista,
                Emprestimos.data_devolucao_real,
                Emprestimos.id_livro_FK,
                Livros.nome_livro
                FROM Emprestimos 
                INNER JOIN Livros ON Emprestimos.id_livro_FK = id_livro WHERE id_usuario_FK = %s;
            """

            cursor.execute(command_emprestimos, (id_usuario_FK,))
            emprestimos = cursor.fetchall()

            if not emprestimos:
                flash('Você ainda não fez nenhum empréstimo')
                emprestimos = []
            
            return render_template('meusEmprestimos.html', emprestimos=emprestimos)

    except Exception as e:
        flash('Erro ao buscar empréstimos')
        return render_template('perfil.html') 
    
@app.route('/AdmEmprestimos')
def AdmEmprestimos():
    email = session.get('email')

    if not email:
        flash('O email é obrigatório')
        return render_template('login.html')
    
    try:
        with connection.cursor() as cursor:
            command_usuario = "SELECT id_usuario FROM Usuarios WHERE email_usuario = %s;"
            cursor.execute(command_usuario, (email,))
            usuario = cursor.fetchone()

            if not usuario:
                flash('Usuário não encontrado')
                return render_template('login.html')
            
            id_usuario_FK = usuario[0]
            command_emprestimos = """
                SELECT 
                Emprestimos.id_emprestimo,
                Emprestimos.data_emprestimo_livro,
                Emprestimos.data_devolucao_prevista,
                Emprestimos.data_devolucao_real,
                Emprestimos.id_livro_FK,
                Livros.nome_livro
                FROM Emprestimos 
                INNER JOIN Livros ON Emprestimos.id_livro_FK = id_livro WHERE id_usuario_FK = %s;
            """

            cursor.execute(command_emprestimos, (id_usuario_FK,))
            emprestimos = cursor.fetchall()

            if not emprestimos:
                flash('Você ainda não fez nenhum empréstimo')
                emprestimos = []
            
            return render_template('AdmEmprestimos.html', emprestimos=emprestimos)

    except Exception as e:
        flash('Erro ao buscar empréstimos')
        return render_template('perfilAdm.html') 
            

@app.route('/livrosUsu')
def livrosUsu():
    command = 'SELECT * FROM Livros;'
    cursor.execute(command)
    livros = cursor.fetchall()

    return render_template('livrosUsu.html', livros=livros)

@app.route('/create/<int:n>', methods=['GET', 'POST'])
def create(n):
    if n == 1:
        if request.method == 'POST':
            nome_livro = request.form['nome_livro']
            autor_livro = request.form['autor_livro']
            data_publicacao_livro = request.form['data_publicacao_livro']
            quantidade_paginas_livro = request.form['quantidade_paginas_livro']
            editora_livro = request.form['editora_livro']
            genero_livro = request.form['genero_livro']
            classificacao_livro = request.form['classificacao_livro']
            isbn_livro = request.form['isbn_livro']
            data_cadastro_livro = request.form['data_cadastro_livro']
            capa_filename = None
            status_livro = request.form['status_livro']

            if 'capa_livro' in request.files:
                capa_livro = request.files['capa_livro']
                if capa_livro:
                    capa_filename = secure_filename(capa_livro.filename)
                    capa_livro.save(os.path.join(app.config['UPLOAD_FOLDER'], capa_filename))
                else:
                    capa_filename = 'default.jpeg'

            command = '''
            INSERT INTO Livros (
            nome_livro, 
            autor_livro, 
            data_publicacao_livro, 
            quantidade_paginas_livro, 
            editora_livro, genero_livro, 
            classificacao_livro, 
            isbn_livro, 
            data_cadastro_livro, 
            status_livro, 
            foto_livro
            ) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            '''
            values = (
                nome_livro, 
                autor_livro, 
                data_publicacao_livro, 
                quantidade_paginas_livro, 
                editora_livro, 
                genero_livro, 
                classificacao_livro, 
                isbn_livro, 
                data_cadastro_livro, 
                status_livro, 
                capa_filename
                )
            
            cursor.execute(command, values)
            connection.commit()
            return redirect('/livros')
    
    elif n == 2:
        if request.method == 'POST': 
            nome_usuario = request.form['nome_usuario']
            cpf_usuario = request.form['cpf_usuario']
            idade_usuario = request.form['idade_usuario']
            telefone_usuario = request.form['telefone_usuario']
            email_usuario = request.form['email_usuario']
            senha_usuario = request.form['senha_usuario']
            funcao_usuario = request.form['funcao_usuario']
            cep_usuario = request.form['cep_usuario']
            numero_casa_usuario = request.form['numero_casa_usuario']

            if not idade_usuario.isdigit() or int(idade_usuario) < 16 or int(idade_usuario) > 80:
                flash("Idade inválida! A idade deve ser um número maior ou igual a 16 e menor que 80.")
                return redirect('/usuarios')
            
            if not validar_nome(nome_usuario): 
                flash("Coloque um nome válido!")
                return redirect('/usuarios')
            
            if not validar_cpf(cpf_usuario): 
                flash("Coloque um CPF válido.")
                return redirect('/usuarios')
            
            if not validar_telefone(telefone_usuario): 
                flash("Coloque um telefone válido.")
                return redirect ('/usuarios')
            
            if not validar_cep(cep_usuario): 
                flash("Coloque um CEP válido.")
                return redirect ('/usuarios')
            
            erro = validar_senha(senha_usuario)
            if erro: 
                flash(erro)
                return redirect ('/usuarios')
            
            salt = gerar_salt()
            senha_hash = hash_senha(senha_usuario, salt)

            try: 
                command = """
                INSERT INTO Usuarios (nome_usuario, cpf_usuario, idade_usuario, telefone_usuario, 
                email_usuario, senha_usuario, funcao_usuario, cep_usuario, numero_casa_usuario, salt) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """
                values = (nome_usuario, cpf_usuario, idade_usuario, telefone_usuario, 
                    email_usuario, senha_hash, funcao_usuario, cep_usuario, 
                    numero_casa_usuario, salt)
            
                cursor.execute(command, values)
                connection.commit()
                return redirect('/usuarios')
            except Exception as e: 
                connection.rollback() 
                flash(f"Erro ao criar o usuário: {str(e)}")
                return redirect('/usuarios')
        return redirect('/usuarios')

    elif n == 3:
        if request.method == 'POST': 
            data_emprestimo_livro = request.form['data_emprestimo_livro']
            data_devolucao_prevista = request.form['data_devolucao_prevista']
            data_devolucao_real = request.form['data_devolucao_real']
            id_livro_FK = request.form['id_livro_FK']
            id_usuario_FK = request.form['id_usuario_FK']

            if verificar_emprestimo_ativo(id_livro_FK):
                flash("Este livro já está emprestado e não pode ser emprestado novamente até que seja devolvido.")
                return redirect('/emprestimos')
            
            erro_data = validar_data_devolucao(data_devolucao_prevista)
            if erro_data: 
                flash(erro_data)
                return redirect('/emprestimos')
            
            erro_emprestimo = validar_data_emprestimo(data_emprestimo_livro)
            if erro_emprestimo: 
                flash(erro_emprestimo)
                return redirect('/emprestimos')
            
            try: 
                if not data_devolucao_real:
                    command = '''
                    INSERT INTO Emprestimos (data_emprestimo_livro, data_devolucao_prevista, data_devolucao_real, id_livro_FK, id_usuario_FK) 
                    VALUES (%s, %s, null, %s, %s);
                    '''
                    cursor.execute(command, (data_emprestimo_livro, data_devolucao_prevista, id_livro_FK, id_usuario_FK))

                else:
                    command = '''
                    INSERT INTO Emprestimos (data_emprestimo_livro, data_devolucao_prevista, data_devolucao_real, id_livro_FK, id_usuario_FK) 
                    VALUES (%s, %s, %s, %s, %s);
                    '''
                    cursor.execute(command, (data_emprestimo_livro, data_devolucao_prevista, id_livro_FK, id_usuario_FK))
                connection.commit()
                pass
                return redirect('/emprestimos')
            except Exception as e: 
                flash(f"Erro ao salvar o empréstimo no banco de dados: {e}")
                return redirect('/emprestimos')

        else: 
            return "Página não encontrada", 404

@app.route('/update/<int:id>/<int:n>', methods=['POST'])
def update(id, n):
    if n == 1:
        id_livro = id

        nome_livro = request.form['nome_livro']
        autor_livro = request.form['autor_livro']
        data_publicacao_livro = request.form['data_publicacao_livro']
        quantidade_paginas_livro = request.form['quantidade_paginas_livro']
        editora_livro = request.form['editora_livro']
        genero_livro = request.form['genero_livro']
        classificacao_livro = request.form['classificacao_livro']
        isbn_livro = request.form['isbn_livro']
        data_cadastro_livro = request.form['data_cadastro_livro']
        capa_filename = None
        status_livro = request.form['status_livro']

        if 'capa_livro' in request.files:
            capa_livro = request.files['capa_livro']
            if capa_livro:
                capa_filename = secure_filename(capa_livro.filename)
                capa_livro.save(os.path.join(app.config['UPLOAD_FOLDER'], capa_filename))
            else:
                capa_filename = 'default.jpeg'

        command = """
            UPDATE Livros 
            SET 
                nome_livro = %s, 
                autor_livro = %s, 
                data_publicacao_livro = %s, 
                quantidade_paginas_livro = %s, 
                editora_livro = %s, 
                genero_livro = %s, 
                classificacao_livro = %s, 
                isbn_livro = %s, 
                data_cadastro_livro = %s, 
                status_livro = %s, 
                foto_livro = %s
            WHERE 
                id_livro = %s;
            """

        values = (
                nome_livro,
                autor_livro,
                data_publicacao_livro,
                quantidade_paginas_livro,
                editora_livro,
                genero_livro,
                classificacao_livro,
                isbn_livro,
                data_cadastro_livro,
                status_livro,
                capa_filename, 
                id_livro
        )

        cursor.execute(command, values)
        connection.commit()
        return redirect('/livros')
    
    elif n == 2:
        if request.method == 'POST': 
            id_usuario = id

            nome_usuario = request.form['nome_usuario']
            cpf_usuario = request.form['cpf_usuario']
            idade_usuario = request.form['idade_usuario']
            telefone_usuario = request.form['telefone_usuario']
            email_usuario = request.form['email_usuario']
            senha_usuario = request.form['senha_usuario']
            funcao_usuario = request.form['funcao_usuario']
            cep_usuario = request.form['cep_usuario']
            numero_casa_usuario = request.form['numero_casa_usuario']

            if not idade_usuario.isdigit() or int(idade_usuario) < 16 or int(idade_usuario) > 80:
                flash("Idade inválida! A idade deve ser um número maior ou igual a 16 e menor que 80.")
                return redirect('/usuarios')
            
            if not validar_nome(nome_usuario): 
                flash("Coloque um nome válido!")
                return redirect('/usuarios')
            
            if not validar_cpf(cpf_usuario): 
                flash("Coloque um CPF válido.")
                return redirect('/usuarios')
            
            if not validar_telefone(telefone_usuario): 
                flash("Coloque um telefone válido.")
                return redirect ('/usuarios')
            
            if not validar_cep(cep_usuario): 
                flash("Coloque um CEP válido.")
                return redirect ('/usuarios')

            command = """
                UPDATE Usuarios
                SET 
                    nome_usuario = %s, 
                    cpf_usuario = %s,
                    idade_usuario = %s, 
                    telefone_usuario = %s, 
                    email_usuario = %s,
                    senha_usuario = %s,
                    funcao_usuario = %s, 
                    cep_usuario = %s, 
                    numero_casa_usuario = %s
                WHERE 
                    id_usuario = %s;
                """

            values = (
                    nome_usuario,
                    cpf_usuario,
                    idade_usuario,
                    telefone_usuario,
                    email_usuario,
                    funcao_usuario,
                    cep_usuario,
                    numero_casa_usuario, 
                    id_usuario
            )

            cursor.execute(command, values)
            connection.commit()
            return redirect('/usuarios')
    
    else:
        id_emprestimo = id

        data_emprestimo_livro = request.form['data_emprestimo_livro']
        data_devolucao_prevista = request.form['data_devolucao_prevista']
        data_devolucao_real = request.form['data_devolucao_real']
        id_livro_FK = request.form['id_livro_FK']
        id_usuario_FK = request.form['id_usuario_FK']

        erro_data = validar_data_devolucao(data_devolucao_prevista)
        if erro_data: 
            flash(erro_data)
            return redirect('/emprestimos')
            
        erro_emprestimo = validar_data_emprestimo(data_emprestimo_livro)
        if erro_emprestimo: 
            flash(erro_emprestimo)
            return redirect('/emprestimos')
        
        if verificar_emprestimo_ativo(id_livro_FK):
            flash("Este livro já está emprestado e não pode ser emprestado novamente até que seja devolvido.")
            return redirect('/emprestimos')

        if not data_devolucao_real:
            command = """
                UPDATE Emprestimos 
                SET 
                    data_emprestimo_livro = %s, 
                    data_devolucao_prevista = %s, 
                    data_devolucao_real = null, 
                    id_livro_FK = %s, 
                    id_usuario_FK = %s
                WHERE 
                    id_emprestimo = %s;
                """

            values = (
                    data_emprestimo_livro,
                    data_devolucao_prevista,
                    id_livro_FK,
                    id_usuario_FK, 
                    id_emprestimo
            )

        else:
            command = """
                UPDATE Emprestimos 
                SET 
                    data_emprestimo_livro = %s, 
                    data_devolucao_prevista = %s, 
                    data_devolucao_real = %s, 
                    id_livro_FK = %s, 
                    id_usuario_FK = %s
                WHERE 
                    id_emprestimo = %s;
                """

            values = (
                    data_emprestimo_livro,
                    data_devolucao_prevista,
                    data_devolucao_real, 
                    id_livro_FK,
                    id_usuario_FK, 
                    id_emprestimo
            )

        cursor.execute(command, values)
        connection.commit()
        return redirect('/emprestimos')

@app.route('/delete/<int:id>/<int:n>')
def delete(id, n):
    if n == 1:
        id_livro = id
        
        try:
            command = f'DELETE FROM Livros WHERE id_livro = {id_livro};'
            cursor.execute(command)
            connection.commit()
        except:
            flash('Não é possível excluir um livro relacionado a um empréstimo.', 'error')
            return redirect(url_for('livros'))

        flash('Livro excluído com sucesso!', 'success')
        return redirect('/livros')
    
    elif n == 2:
        id_usuario = id

        try:
            command = f'DELETE FROM Usuarios WHERE id_usuario = {id_usuario};'
            cursor.execute(command)
            connection.commit()
        except:
            flash('Não é possível excluir um usuário relacionado a um empréstimo.', 'error')
            return redirect(url_for('usuarios'))

        flash('Usuário excluído com sucesso!', 'success')
        return redirect('/usuarios')
    
    else:
        id_emprestimo = id

        command = f'DELETE FROM Emprestimos WHERE id_emprestimo = {id_emprestimo};'
        cursor.execute(command)
        connection.commit()

        flash('Empréstimo excluído com sucesso!', 'success')
        return redirect('/emprestimos')

@app.route('/pesquisar/<int:n>', methods=['POST'])
def pesquisar(n):
    if n == 1:
        pesquisa = request.form['pesquisa']
        if not pesquisa:
            command = 'SELECT * FROM Livros;'
            cursor.execute(command)
            livros = cursor.fetchall()

            return render_template('livros.html', livros=livros)

        try:
            pesquisa = int(pesquisa)

            command = 'SELECT * FROM Livros WHERE isbn_livro LIKE %s;'
            cursor.execute(command, (f'%{pesquisa}%',))
            livros = cursor.fetchall()
        
            return render_template('livros.html', livros=livros)
        except:
            command = 'SELECT * FROM Livros WHERE nome_livro LIKE %s OR autor_livro LIKE %s COLLATE utf8mb4_general_ci;'
            cursor.execute(command, (f'%{pesquisa}%', f'%{pesquisa}%'))
            livros = cursor.fetchall()
        
            return render_template('livros.html', livros=livros)
    
    elif n == 2:
        pesquisa = request.form['pesquisa']
        if not pesquisa:
            command = 'SELECT * FROM Usuarios;'
            cursor.execute(command)
            usuarios = cursor.fetchall()

            return render_template('usuarios.html', usuarios=usuarios)

        command = 'SELECT * FROM Usuarios WHERE nome_usuario LIKE %s COLLATE utf8mb4_general_ci;'
        cursor.execute(command, (f'%{pesquisa}%',))
        usuarios = cursor.fetchall()
        
        return render_template('usuarios.html', usuarios=usuarios)
    
    else:
        data_emprestimo = request.form['data_emprestimo']
        data_devolucao = request.form['data_devolucao']

        if not data_emprestimo and not data_devolucao:
            command = 'SELECT * FROM Emprestimos;'
            cursor.execute(command)
            emprestimos = cursor.fetchall()

            return render_template('emprestimos.html', emprestimos=emprestimos)
        
        print(data_devolucao, data_emprestimo)

        try:
            command = "SELECT * FROM Emprestimos WHERE data_emprestimo_livro = %s OR data_devolucao_prevista = %s;"
            cursor.execute(command, (f'{data_emprestimo}', f'{data_devolucao}'))
            emprestimos = cursor.fetchall()
        except:
            if data_emprestimo == '':
                command = "SELECT * FROM Emprestimos WHERE data_devolucao_prevista = %s;"
                cursor.execute(command, (f'{data_devolucao}',))
                emprestimos = cursor.fetchall()
            else:
                command = "SELECT * FROM Emprestimos WHERE data_emprestimo_livro = %s;"
                cursor.execute(command, (f'{data_emprestimo}',))
                emprestimos = cursor.fetchall()

        return render_template('emprestimos.html', emprestimos=emprestimos)

@app.route('/ver_livro_usuario/<int:id>/<int:n>')
def ver_livro_usuario(id, n):
    if n == 4:
        command = "SELECT * FROM Livros WHERE id_livro = %s;"
        cursor.execute(command, (f'{id}',))
        livros = cursor.fetchall()

        return render_template('livros.html', livros=livros)
    
    else:
        command = "SELECT * FROM Usuarios WHERE id_usuario = %s;"
        cursor.execute(command, (f'{id}',))
        usuarios = cursor.fetchall()

        return render_template('usuarios.html', usuarios=usuarios)

@app.route('/relatorio_livros')
def relatorio_livros():
    command = 'SELECT * FROM Livros;'
    cursor.execute(command)
    livros = cursor.fetchall()

    return render_template('relatorioLivros.html', livros=livros)


@app.route('/gerar_relatorio_livros', methods=['POST'])
def gerar_relatorio_livros():
    autor = request.form['autor']
    genero = request.form['genero']
    datacadastro = request.form['datacadastro']
    classificacao = request.form['classificacao']
    status = request.form['status']

    command = "SELECT * FROM Livros;"
    cursor.execute(command)
    livros = cursor.fetchall()

    livros_filtrados = [
        livro for livro in livros
        if (autor == "todos" or livro[2] == autor)
        and (genero == "todos" or livro[6] == genero)
        and (datacadastro == "todos" or livro[9] == datacadastro)
        and (classificacao == "todos" or livro[7] == classificacao)
        and (status == "todos" or livro[11] == status)
    ]

    total_livros = len(livros_filtrados)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    title = Paragraph("Relatório de Livros", styles['Title'])
    elements.append(title)

    data = [["Título", "Autor", "Gênero", "Data Cadastro", "Classificação", "Status"]] 
    for livro in livros_filtrados:
        data.append([livro[1], livro[2], livro[6], livro[9], livro[7], livro[11]])

    table = Table(data, colWidths=[100, 100, 80, 80, 80, 80])
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey), 
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'), 
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige), 
    ])
    table.setStyle(style)
    elements.append(table)

    elements.append(Paragraph(" ", styles['Normal']))
    elements.append(Paragraph(f"Total de livros no relatório: {total_livros}", styles['Normal']))
    elements.append(Paragraph(" ", styles['Normal'])) 
    footer = Paragraph("Relatório gerado automaticamente em: " + datetime.now().strftime('%d/%m/%Y %H:%M:%S'), styles['Normal'])
    elements.append(footer)

    doc.build(elements)
    buffer.seek(0)
    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=relatorio_livros.pdf'
    return response

@app.route('/relatorio_emprestimos')
def relatorio_emprestimos():
    command = 'SELECT * FROM Livros;'
    cursor.execute(command)
    livros = cursor.fetchall()

    command = 'SELECT * FROM Usuarios;'
    cursor.execute(command)
    usuarios = cursor.fetchall()

    return render_template('relatorioEmprestimos.html', livros=livros, usuarios=usuarios)

@app.route('/gerar_relatorio_emprestimos', methods=['POST'])
def gerar_relatorio_emprestimos():
    titulo = request.form['livro']
    autor = request.form['autor']
    genero = request.form['genero']

    command = "SELECT id_livro, nome_livro, autor_livro, genero_livro FROM Livros;"
    cursor.execute(command)
    livros = cursor.fetchall()

    command = "SELECT id_livro_FK FROM Emprestimos;"
    cursor.execute(command)
    emprestimos = cursor.fetchall()

    emprestimos_por_livro = {}
    for emprestimo in emprestimos:
        livro_id = emprestimo[0]
        if livro_id in emprestimos_por_livro:
            emprestimos_por_livro[livro_id] += 1
        else:
            emprestimos_por_livro[livro_id] = 1

    livros_filtrados = [
        livro for livro in livros
        if (autor == "todos" or livro[2] == autor)
        and (titulo == "todos" or livro[1] == titulo)
        and (genero == "todos" or livro[3] == genero)
    ]

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    title = Paragraph("Relatório de Empréstimos por Livro", styles['Title'])
    elements.append(title)
    elements.append(Paragraph(" ", styles['Normal']))

    data = [["Título", "Autor", "Gênero", "Empréstimos"]]

    for livro in livros_filtrados:
        livro_id = livro[0]
        total_emprestimos = emprestimos_por_livro.get(livro_id, 0)
        data.append([livro[1], livro[2], livro[3], total_emprestimos])

    table = Table(data, colWidths=[150, 150, 100, 100])
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey), 
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), 
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'), 
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12), 
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    ])
    table.setStyle(style)
    elements.append(table)

    elements.append(Paragraph(" ", styles['Normal']))
    footer = Paragraph(
        "Relatório gerado automaticamente em: " +
        datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        styles['Normal']
    )
    elements.append(footer)

    doc.build(elements)
    buffer.seek(0)
    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=relatorio_emprestimos.pdf'
    return response

def hash_senha(senha, salt):
    senha_salt = senha + salt
    hash_object = hashlib.sha256(senha_salt.encode())
    return hash_object.hexdigest()

def gerar_salt():
    return secrets.token_hex(16)

def validar_nome(nome):
    padrao =  r'^[a-zA-ZáéíóúãõâêîôûàèìòùäëïöüçÇ\s]{3,100}$'
    if re.match(padrao, nome):
        return True
    else:
        return False 
    
def validar_cpf(cpf):
    cpf = re.sub(r'\D', '', cpf)

    if len(cpf) != 11 or cpf == "00000000000" or cpf == "11111111111" or cpf == "22222222222" or \
       cpf == "33333333333" or cpf == "44444444444" or cpf == "55555555555" or cpf == "66666666666" or \
       cpf == "77777777777" or cpf == "88888888888" or cpf == "99999999999":
        return False

    soma = 0
    for i in range(9):
        soma += int(cpf[i]) * (10 - i)
    primeiro_digito = (soma * 10) % 11
    if primeiro_digito == 10:
        primeiro_digito = 0
    if int(cpf[9]) != primeiro_digito:
        return False

    soma = 0
    for i in range(10):
        soma += int(cpf[i]) * (11 - i)
    segundo_digito = (soma * 10) % 11
    if segundo_digito == 10:
        segundo_digito = 0
    if int(cpf[10]) != segundo_digito:
        return False

    return True

def validar_telefone(telefone):
    telefone = re.sub(r'\D', '', telefone)

    if len(telefone) != 11 and len(telefone) != 10:
        return False

    if len(telefone) == 11:  
        if telefone[2] != '9':
            return False
    elif len(telefone) == 10:  
        if telefone[2] in '9':
            return False

    return True

def validar_cep(cep):
    cep = re.sub(r'\D', '', cep)
    
    if len(cep) != 8:
        return False
    
    if not cep.isdigit():
        return False
    
    return True

def validar_senha(senha):
    if len(senha) < 8:
        return "A senha deve ter pelo menos 8 caracteres."
    if not re.search(r'[A-Z]', senha):
        return "A senha deve conter pelo menos uma letra maiúscula."
    if not re.search(r'[\W_]', senha):
        return "A senha deve conter pelo menos um caractere especial."
    return None

def validar_data_emprestimo(data_emprestimo_str):
    try:
        data_emprestimo = datetime.strptime(data_emprestimo_str, '%Y-%m-%d').date()
        data_atual = datetime.now().date()

        if data_emprestimo < data_atual:
            return "A data de empréstimo não pode ser uma data passada."
        
        if data_emprestimo > data_atual + timedelta(days=15):
            return "A data de empréstimo não pode ser mais de 15 dias à frente."
        
        return None
    except ValueError:
        return "Formato de data inválido. Use o formato 'YYYY-MM-DD'."
    
def validar_data_devolucao(data_devolucao_str):
    try:
        data_devolucao = datetime.strptime(data_devolucao_str, '%Y-%m-%d').date()
        data_atual = datetime.now().date()

        if data_devolucao < data_atual:
            return "A data de devolução não pode ser uma data passada."
        
        if data_devolucao > data_atual + timedelta(days=15):
            return "A data de devolução não pode ser mais de 15 dias à frente."
        
        return None
    except ValueError:
        return "Formato de data inválido. Use o formato 'YYYY-MM-DD'."

def verificar_emprestimo_ativo(id_livro):
    try:
        query = """
            SELECT COUNT(*) FROM emprestimos 
            WHERE id_livro_FK = %s AND data_devolucao_real IS NULL
        """
        cursor.execute(query, (id_livro,))
        resultado = cursor.fetchone()
        
        if resultado[0] > 0:
            return True
        else:
            return False
    except Exception as e:  
        print(f"Erro ao acessar o banco de dados: {e}")
        return False

if __name__ == '__main__':
    app.run(debug=True)
