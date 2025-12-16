package com.biostar.camtest

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.util.Size
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.core.CameraSelector
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.google.common.util.concurrent.ListenableFuture
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

class MainActivity : AppCompatActivity() {
    
    private lateinit var previewView: PreviewView
    private lateinit var btnStart: Button
    private lateinit var btnStop: Button
    private lateinit var btnFullscreen: Button
    private lateinit var cameraProviderFuture: ListenableFuture<ProcessCameraProvider>
    private lateinit var cameraExecutor: ExecutorService
    private var cameraProvider: ProcessCameraProvider? = null
    private var isFullscreen = false
    
    companion object {
        private const val REQUEST_CODE_PERMISSIONS = 10
        private val REQUIRED_PERMISSIONS = arrayOf(Manifest.permission.CAMERA)
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        // Mantener pantalla encendida
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        
        // Inicializar vistas
        previewView = findViewById(R.id.previewView)
        btnStart = findViewById(R.id.btnStart)
        btnStop = findViewById(R.id.btnStop)
        btnFullscreen = findViewById(R.id.btnFullscreen)
        
        cameraExecutor = Executors.newSingleThreadExecutor()
        
        // Configurar botones
        btnStart.setOnClickListener {
            if (allPermissionsGranted()) {
                startCamera()
            } else {
                ActivityCompat.requestPermissions(
                    this, REQUIRED_PERMISSIONS, REQUEST_CODE_PERMISSIONS
                )
            }
        }
        
        btnStop.setOnClickListener {
            stopCamera()
        }
        
        btnFullscreen.setOnClickListener {
            toggleFullscreen()
        }
        
        // Verificar permisos al inicio
        if (allPermissionsGranted()) {
            btnStart.isEnabled = true
        }
    }
    
    private fun startCamera() {
        cameraProviderFuture = ProcessCameraProvider.getInstance(this)
        
        cameraProviderFuture.addListener({
            try {
                cameraProvider = cameraProviderFuture.get()
                bindPreview(cameraProvider!!)
                
                // Actualizar UI
                btnStart.visibility = View.GONE
                btnStop.visibility = View.VISIBLE
                btnFullscreen.visibility = View.VISIBLE
                
                Toast.makeText(this, "Cámara iniciada", Toast.LENGTH_SHORT).show()
            } catch (e: Exception) {
                Toast.makeText(this, "Error: ${e.message}", Toast.LENGTH_LONG).show()
            }
        }, ContextCompat.getMainExecutor(this))
    }
    
    private fun bindPreview(cameraProvider: ProcessCameraProvider) {
        // Configurar preview con máxima calidad
        val preview = Preview.Builder()
            .setTargetResolution(Size(1920, 1080))
            .build()
        
        // Seleccionar cámara trasera por defecto
        val cameraSelector = CameraSelector.Builder()
            .requireLensFacing(CameraSelector.LENS_FACING_BACK)
            .build()
        
        preview.setSurfaceProvider(previewView.surfaceProvider)
        
        try {
            // Desenlazar casos de uso anteriores
            cameraProvider.unbindAll()
            
            // Enlazar casos de uso a la cámara
            cameraProvider.bindToLifecycle(
                this,
                cameraSelector,
                preview
            )
        } catch (e: Exception) {
            Toast.makeText(this, "Error al enlazar cámara: ${e.message}", Toast.LENGTH_LONG).show()
        }
    }
    
    private fun stopCamera() {
        cameraProvider?.unbindAll()
        
        // Actualizar UI
        btnStart.visibility = View.VISIBLE
        btnStop.visibility = View.GONE
        btnFullscreen.visibility = View.GONE
        
        // Salir de fullscreen si está activo
        if (isFullscreen) {
            toggleFullscreen()
        }
        
        Toast.makeText(this, "Cámara detenida", Toast.LENGTH_SHORT).show()
    }
    
    private fun toggleFullscreen() {
        isFullscreen = !isFullscreen
        
        if (isFullscreen) {
            // Entrar a fullscreen
            window.decorView.systemUiVisibility = (
                View.SYSTEM_UI_FLAG_FULLSCREEN
                or View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                or View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
            )
            supportActionBar?.hide()
            btnFullscreen.text = "Salir Pantalla Completa"
        } else {
            // Salir de fullscreen
            window.decorView.systemUiVisibility = View.SYSTEM_UI_FLAG_VISIBLE
            supportActionBar?.show()
            btnFullscreen.text = "Pantalla Completa"
        }
    }
    
    private fun allPermissionsGranted() = REQUIRED_PERMISSIONS.all {
        ContextCompat.checkSelfPermission(baseContext, it) == PackageManager.PERMISSION_GRANTED
    }
    
    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == REQUEST_CODE_PERMISSIONS) {
            if (allPermissionsGranted()) {
                startCamera()
            } else {
                Toast.makeText(
                    this,
                    "Permisos de cámara denegados",
                    Toast.LENGTH_SHORT
                ).show()
                finish()
            }
        }
    }
    
    override fun onDestroy() {
        super.onDestroy()
        cameraExecutor.shutdown()
    }
}
