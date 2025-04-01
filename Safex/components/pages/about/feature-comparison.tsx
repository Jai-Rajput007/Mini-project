"use client";
import { useState } from "react";
import Image from "next/image";
import { Badge } from "@/components/common/badge";
import { GripVertical } from "lucide-react";

function FeatureComparison() {
  const [inset, setInset] = useState<number>(50);
  const [onMouseDown, setOnMouseDown] = useState<boolean>(false);

  const onMouseMove = (e: React.MouseEvent | React.TouchEvent) => {
    if (!onMouseDown) return;

    const rect = e.currentTarget.getBoundingClientRect();
    let x = 0;

    if ("touches" in e && e.touches.length > 0) {
      x = e.touches[0].clientX - rect.left;
    } else if ("clientX" in e) {
      x = e.clientX - rect.left;
    }
    
    const percentage = (x / rect.width) * 100;
    setInset(percentage);
  };

  return (
    <section className="w-full bg-background py-8">
      <div className="max-w-5xl mx-auto px-4 sm:px-6">
        <div className="relative overflow-hidden w-full rounded-xl border border-border">
          {/* Base container with fixed height */}
          <div 
            className="relative w-full h-[350px] md:h-[400px]"
            onMouseMove={onMouseMove}
            onMouseUp={() => setOnMouseDown(false)}
            onTouchMove={onMouseMove}
            onTouchEnd={() => setOnMouseDown(false)}
          >
            {/* Dark theme (base layer) */}
            <div className="absolute inset-0 safex-feature-dark">
              <div className="flex flex-col md:flex-row h-full">
                {/* Text content */}
                <div className="w-full md:w-1/2 p-5 md:p-8 flex flex-col justify-center">
                  <Badge className="mb-2 safex-feature-badge-dark w-fit text-xs">Security Platform</Badge>
                  <h2 className="text-xl md:text-2xl font-medium safex-feature-text-dark mb-2">
                    Advanced Phishing Detection
                  </h2>
                  <p className="safex-feature-muted-text-dark leading-relaxed text-sm">
                    Our platform uses advanced algorithms to detect phishing attempts in real-time, protecting your sensitive data.
                  </p>
                </div>
                
                {/* Image content */}
                <div className="w-full md:w-1/2 p-5 flex items-center justify-center">
                  <div className="bg-secondary w-full h-[180px] md:h-[250px] flex items-center justify-center overflow-hidden rounded-lg">
                    <Image 
                      src="/Ransomeware.jpg"
                      alt="Ransomware attack example - dark mode"
                      width={500}
                      height={300}
                      className="w-full h-full object-cover"
                    />
                  </div>
                </div>
              </div>
            </div>
            
            {/* Light theme (overlay) */}
            <div 
              className="absolute inset-0 safex-feature-light z-10"
              style={{
                clipPath: `inset(0 ${100 - inset}% 0 0)`,
              }}
            >
              <div className="flex flex-col md:flex-row h-full">
                {/* Text content */}
                <div className="w-full md:w-1/2 p-5 md:p-8 flex flex-col justify-center">
                  <Badge className="mb-2 safex-feature-badge-light w-fit text-xs">Security Platform</Badge>
                  <h2 className="text-xl md:text-2xl font-medium safex-feature-text-light mb-2">
                    Advanced Phishing Detection
                  </h2>
                  <p className="safex-feature-muted-text-light leading-relaxed text-sm">
                    Our platform uses advanced algorithms to detect phishing attempts in real-time, protecting your sensitive data.
                  </p>
                </div>
                
                {/* Image content */}
                <div className="w-full md:w-1/2 p-5 flex items-center justify-center">
                  <div className="bg-secondary/30 w-full h-[180px] md:h-[250px] flex items-center justify-center overflow-hidden rounded-lg">
                    <Image 
                      src="/Attacked.jpg"
                      alt="Phishing attack example - light mode"
                      width={500}
                      height={300}
                      className="w-full h-full object-cover"
                    />
                  </div>
                </div>
              </div>
            </div>
            
            {/* Divider line */}
            <div
              className="absolute top-0 bottom-0 w-0.5 safex-feature-divider z-20"
              style={{ left: `${inset}%` }}
            >
              {/* Slider handle */}
              <button
                className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-5 h-10 rounded-full safex-feature-handle flex items-center justify-center z-30 cursor-ew-resize shadow-md"
                aria-label="Drag to compare light and dark themes"
                onTouchStart={(e) => {
                  setOnMouseDown(true);
                  onMouseMove(e);
                }}
                onMouseDown={(e) => {
                  setOnMouseDown(true);
                  onMouseMove(e);
                }}
                onTouchEnd={() => setOnMouseDown(false)}
                onMouseUp={() => setOnMouseDown(false)}
              >
                <GripVertical className="h-3 w-3 text-gray-500" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export { FeatureComparison }; 